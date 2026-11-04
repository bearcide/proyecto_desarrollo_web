"""Importación local: mismo camino transaccional para validar y confirmar."""
import csv
import io
import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.core.models import Alumno, Grupo, MembresiaTenant, Nodo, PlanEstudios, SolicitudMateria
from apps.core.services.errors import ReglaDeNegocioError
from apps.core.services.prerrequisitos import crear_prerrequisito

COLUMNAS = {
    'planes': {'nombre', 'descripcion'},
    'materias': {'plan', 'clave', 'nombre', 'creditos', 'semestre', 'prerrequisitos'},
    'alumnos': {'matricula', 'nombre', 'apellido_paterno', 'apellido_materno', 'plan', 'aprobadas', 'password'},
    'grupos': {'materia', 'clave', 'profesor', 'cupo', 'horarios'},
    'solicitudes': {'matricula', 'materia', 'preferencia', 'prioridad_institucional'},
}
DIAS = {'Lunes':'Lunes','Martes':'Martes','Miercoles':'Miércoles','Miércoles':'Miércoles',
        'Jueves':'Jueves','Viernes':'Viernes','Sabado':'Sábado','Sábado':'Sábado','Domingo':'Domingo'}


class ErrorImportacion(Exception):
    def __init__(self, informe):
        self.informe = informe
        super().__init__('El CSV contiene errores; no se importaron datos.')


class ErrorFila(ValueError):
    def __init__(self, campo, mensaje):
        self.campo = campo
        super().__init__(mensaje)


def texto(row, campo, maximo=150, obligatorio=True):
    value = row[campo].strip()
    if (obligatorio and not value) or len(value) > maximo:
        raise ErrorFila(campo, f'Valor requerido de hasta {maximo} caracteres.' if obligatorio else f'Máximo {maximo} caracteres.')
    return value


def entero(row, campo, minimo=0):
    try:
        value = int(row[campo])
        if value < minimo or value > 2147483647:
            raise ValueError()
        return value
    except (ValueError, TypeError):
        raise ErrorFila(campo, f'Se requiere entero >= {minimo}.')


def bloques(value):
    result=[]
    for item in value.split(';'):
        match=re.fullmatch(r'([^:]+):(\d{2}):(\d{2})-(\d{2}):(\d{2})', item.strip())
        if not match or match[1] not in DIAS:
            raise ErrorFila('horarios', 'Formato requerido: Lunes:08:00-10:00;Martes:10:00-12:00.')
        h1,m1,h2,m2=map(int,match.groups()[1:])
        if h1>23 or h2>23 or m1>59 or m2>59:
            raise ErrorFila('horarios','Hora fuera de rango 00:00..23:59.')
        start,end=h1*60+m1,h2*60+m2
        if start>=end:
            raise ErrorFila('horarios','El final debe ser posterior al inicio.')
        block={'dia':DIAS[match[1]],'inicio':start,'fin':end}
        if any(b['dia']==block['dia'] and b['inicio']<end and start<b['fin'] for b in result):
            raise ErrorFila('horarios','Bloques del mismo grupo se solapan.')
        result.append(block)
    return result


def referencia(model, tenant, campo, value, error_campo):
    obj=model.objects.filter(tenant=tenant, **{campo:value.strip()}).first()
    if obj is None:
        raise ErrorFila(error_campo,'Referencia no encontrada en esta escuela.')
    return obj


def claves(value, tenant, campo):
    result=[]
    for clave in filter(None,(s.strip() for s in value.split(';'))):
        obj=referencia(Nodo,tenant,'clave',clave,campo)
        if obj.pk not in [x.pk for x in result]: result.append(obj)
    return result


def parsear(archivos):
    report={'valido':True,'filas':{},'errores':[]}
    parsed={}
    if not isinstance(archivos,dict) or not archivos or set(archivos)-set(COLUMNAS):
        raise ErrorFila('archivos','Se requiere un objeto con al menos un CSV de tipo conocido.')
    if any(not isinstance(t,str) for t in archivos.values()) or sum(len(t.encode('utf-8')) for t in archivos.values())>2_000_000:
        raise ErrorFila('archivos','Solo texto UTF-8; máximo 2 MB en total.')
    for name,content in archivos.items():
        try:
            reader=csv.DictReader(io.StringIO(content.lstrip('\ufeff')),strict=True)
            if not reader.fieldnames or set(reader.fieldnames)!=COLUMNAS[name] or len(reader.fieldnames)!=len(COLUMNAS[name]):
                raise ErrorFila('encabezado','Columnas exactas requeridas: '+','.join(sorted(COLUMNAS[name])))
            rows=[]
            for number,row in enumerate(reader,2):
                if number>10001: raise ErrorFila('archivo','Máximo 10000 filas por archivo.')
                if None in row or any(v is None for v in row.values()):
                    report['errores'].append({'archivo':name,'fila':number,'campo':'fila','mensaje':'Número de columnas incorrecto.'})
                else: rows.append((number,row))
            report['filas'][name]=len(rows)
            parsed[name]=rows
        except (csv.Error,ErrorFila) as exc:
            report['errores'].append({'archivo':name,'fila':1,'campo':getattr(exc,'campo','archivo'),'mensaje':str(exc)})
    report['valido']=not report['errores']
    return parsed,report


def importar(tenant, archivos, confirmar=False):
    try:
        parsed,report=parsear(archivos)
    except ErrorFila as exc:
        raise ErrorImportacion({'valido':False,'filas':{},'errores':[{'archivo':'archivos','fila':1,'campo':exc.campo,'mensaje':str(exc)}]})
    if report['errores']: raise ErrorImportacion(report)
    seen={}
    def guardar(name, number, row, action, key):
        try:
            if key in seen.setdefault(name,set()):
                raise ErrorFila('fila','Clave natural duplicada dentro del CSV.')
            seen[name].add(key)
            with transaction.atomic(): action(row)
        except (ErrorFila,ValidationError,ReglaDeNegocioError,IntegrityError) as exc:
            message='Conflicto de integridad o referencia duplicada.' if isinstance(exc,IntegrityError) else str(exc)
            report['errores'].append({'archivo':name,'fila':number,'campo':getattr(exc,'campo','fila'),'mensaje':message})
    with transaction.atomic():
        # Bloqueo común con generación/publicación. SQLite serializa escrituras.
        from apps.core.models import Tenant
        Tenant.objects.select_for_update().get(pk=tenant.pk)
        def plan(row):
            PlanEstudios.objects.update_or_create(tenant=tenant,nombre=texto(row,'nombre'),defaults={'descripcion':texto(row,'descripcion',10000,False)})
        for number,row in parsed.get('planes',[]):
            guardar('planes',number,row,plan,row['nombre'].strip())
        def materia(row):
            p=referencia(PlanEstudios,tenant,'nombre',row['plan'],'plan')
            n=Nodo.objects.filter(tenant=tenant,clave=texto(row,'clave',30)).first()
            if n and n.plan_estudios_id!=p.pk:
                raise ErrorFila('plan','No se cambia el plan de una materia existente por importación.')
            Nodo.objects.update_or_create(tenant=tenant,clave=row['clave'].strip(),defaults={'plan_estudios':p,'nombre':texto(row,'nombre'),'creditos':entero(row,'creditos'),'semestre':entero(row,'semestre',1)})
        for number,row in parsed.get('materias',[]):
            guardar('materias',number,row,materia,row['clave'].strip())
        # Segunda pasada: permite referenciar materias posteriores en el mismo CSV.
        for number,row in parsed.get('materias',[]):
            try:
                with transaction.atomic():
                    n=referencia(Nodo,tenant,'clave',row['clave'],'clave')
                    for required in claves(row['prerrequisitos'],tenant,'prerrequisitos'):
                        if not n.aristas_prerrequisito.filter(prerrequisito=required).exists():
                            crear_prerrequisito(tenant=tenant,nodo=n,prerrequisito=required)
            except (ErrorFila,ReglaDeNegocioError,IntegrityError) as exc:
                report['errores'].append({'archivo':'materias','fila':number,'campo':'prerrequisitos','mensaje':str(exc)})
        def alumno(row):
            account=texto(row,'matricula',32)
            p=referencia(PlanEstudios,tenant,'nombre',row['plan'],'plan')
            approved=claves(row['aprobadas'],tenant,'aprobadas')
            if any(n.plan_estudios_id!=p.pk for n in approved): raise ErrorFila('aprobadas','Materia de otro plan.')
            a=Alumno.objects.filter(tenant=tenant,numero_de_cuenta=account).first()
            U=get_user_model(); user=U.objects.filter(username=account).first()
            if user and (not a or a.user_id!=user.pk):
                raise ErrorFila('matricula','Identificador de usuario existente no asociado a este alumno; requiere revisión explícita.')
            if a and a.user_id and (not user or user.pk!=a.user_id):
                raise ErrorFila('matricula','La asociación de usuario existente no coincide.')
            if user is None:
                password=texto(row,'password',128)
                if len(password)<8: raise ErrorFila('password','Mínimo 8 caracteres para usuarios nuevos.')
                user=U.objects.create_user(username=account,password=password)
            values={'user':user,'plan_estudios':p,'nombre':texto(row,'nombre',100),
                    'apellido_paterno':texto(row,'apellido_paterno',100),'apellido_materno':texto(row,'apellido_materno',100,False),
                    'materias_aprobadas_ids':[n.pk for n in approved]}
            Alumno.objects.update_or_create(tenant=tenant,numero_de_cuenta=account,defaults=values)
            MembresiaTenant.objects.get_or_create(user=user,tenant=tenant,defaults={'es_alumno':True,'es_administrador':False})
        for number,row in parsed.get('alumnos',[]):
            guardar('alumnos',number,row,alumno,row['matricula'].strip())
        def grupo(row):
            n=referencia(Nodo,tenant,'clave',row['materia'],'materia')
            Grupo.objects.update_or_create(tenant=tenant,nodo=n,clave=texto(row,'clave',50),defaults={
                'profesor':texto(row,'profesor',150),'cupo':entero(row,'cupo'),'horarios':bloques(row['horarios'])})
        for number,row in parsed.get('grupos',[]):
            guardar('grupos',number,row,grupo,(row['materia'].strip(),row['clave'].strip()))
        def solicitud(row):
            a=referencia(Alumno,tenant,'numero_de_cuenta',row['matricula'],'matricula')
            n=referencia(Nodo,tenant,'clave',row['materia'],'materia')
            if n.plan_estudios_id!=a.plan_estudios_id: raise ErrorFila('materia','Materia de otro plan de estudios.')
            SolicitudMateria.objects.update_or_create(tenant=tenant,alumno=a,nodo=n,defaults={
                'preferencia':entero(row,'preferencia',1),'prioridad_institucional':entero(row,'prioridad_institucional')})
        for number,row in parsed.get('solicitudes',[]):
            guardar('solicitudes',number,row,solicitud,(row['matricula'].strip(),row['materia'].strip()))
        from django.db.models import Count
        ambiguos=SolicitudMateria.objects.filter(tenant=tenant).values('alumno_id').annotate(prioridades=Count('prioridad_institucional',distinct=True)).filter(prioridades__gt=1)
        if ambiguos.exists(): report['errores'].append({'archivo':'solicitudes','fila':1,'campo':'prioridad_institucional','mensaje':'Todas las solicitudes de un alumno deben tener la misma prioridad institucional.'})
        report['valido']=not report['errores']
        if not confirmar or not report['valido']: transaction.set_rollback(True)
    if not report['valido']: raise ErrorImportacion(report)
    if confirmar: report['importado']=True
    return report
