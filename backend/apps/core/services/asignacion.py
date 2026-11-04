"""Motor greedy determinista, con política institucional explícita y snapshots."""
from collections import Counter, defaultdict
from django.db import transaction
from apps.core.models import Alumno, EjecucionAsignacion, Grupo, ResultadoAsignacion, SolicitudMateria, Tenant
from apps.core.services.errors import ReglaDeNegocioError


def choque(a,b):
    return any(x['dia']==y['dia'] and x['inicio']<y['fin'] and y['inicio']<x['fin'] for x in a for y in b)


def serializar_ejecucion(run):
    return {'id':run.pk,'estado':run.estado,'resumen':run.resumen,'politica':run.politica,'created_at':run.created_at.isoformat()}


def serializar_resultado(row):
    return {'alumno':row.alumno_id,'matricula':row.detalle.get('matricula'),
            'materia':row.nodo_id,'clave_materia':row.detalle.get('clave_materia'),
            'grupo':row.grupo_id,'estado':row.estado,'motivo':row.motivo,'detalle':row.detalle}


@transaction.atomic
def generar(tenant):
    Tenant.objects.select_for_update().get(pk=tenant.pk)
    requests=list(SolicitudMateria.objects.filter(tenant=tenant,alumno__activo=True).select_related('alumno','nodo','alumno__plan_estudios').prefetch_related('nodo__prerrequisitos'))
    por_alumno=defaultdict(list)
    for req in requests:
        if req.alumno.tenant_id!=tenant.pk or req.nodo.tenant_id!=tenant.pk:
            raise ReglaDeNegocioError('Referencia académica fuera de escuela; requiere revisión.')
        por_alumno[req.alumno_id].append(req)
    if not requests: raise ReglaDeNegocioError('No hay solicitudes activas para generar asignaciones.')
    for entries in por_alumno.values():
        if len({x.prioridad_institucional for x in entries})!=1:
            raise ReglaDeNegocioError('Prioridad institucional ambigua para un alumno.')
    ordered=sorted(por_alumno.values(),key=lambda rs:(rs[0].prioridad_institucional,rs[0].alumno.numero_de_cuenta or '',rs[0].alumno_id))
    policy={'version':'greedy-v1','orden_alumnos':['prioridad_institucional ASC','matricula ASC','alumno_id ASC'],
            'orden_materias':['preferencia ASC','clave ASC'],'orden_grupos':['clave ASC','id ASC'],
            'alcance':'propuesta completa por escuela; cupos independientes entre ejecuciones',
            'prioridades':[{'alumno':rs[0].alumno_id,'matricula':rs[0].alumno.numero_de_cuenta,'prioridad':rs[0].prioridad_institucional} for rs in ordered]}
    run=EjecucionAsignacion.objects.create(tenant=tenant,politica=policy,resumen={})
    grupos=defaultdict(list)
    for g in Grupo.objects.filter(tenant=tenant,nodo__tenant=tenant).order_by('clave','pk'):
        grupos[g.nodo_id].append(g)
    policy['oferta']=[{'grupo':g.pk,'materia':g.nodo_id,'clave':g.clave,'cupo':g.cupo,'horarios':g.horarios} for gs in grupos.values() for g in gs]
    usados=Counter(); resultados=[]; counters=Counter()
    for entries in ordered:
        alumno=entries[0].alumno
        aprobadas=set(alumno.materias_aprobadas_ids or [])
        horario=[]
        for req in sorted(entries,key=lambda r:(r.preferencia,r.nodo.clave,r.nodo_id)):
            n=req.nodo; elegido=None; motivo=''
            if n.plan_estudios_id!=alumno.plan_estudios_id or not alumno.plan_estudios.activo:
                motivo='PLAN_INCORRECTO'
            elif n.pk in aprobadas: motivo='YA_APROBADA'
            elif not {p.pk for p in n.prerrequisitos.all()}.issubset(aprobadas): motivo='PRERREQUISITOS'
            elif not grupos[n.pk]: motivo='SIN_GRUPO'
            else:
                disponibles=[g for g in grupos[n.pk] if usados[g.pk]<g.cupo]
                if not disponibles: motivo='SIN_CUPO'
                else:
                    elegido=next((g for g in disponibles if not choque(horario,g.horarios)),None)
                    if elegido is None: motivo='CONFLICTO_HORARIO'
            detalle={'matricula':alumno.numero_de_cuenta,'nombre_materia':n.nombre,'clave_materia':n.clave,
                     'preferencia':req.preferencia,'prioridad_institucional':req.prioridad_institucional,
                     'plan_estudios':alumno.plan_estudios_id,'plan_materia':n.plan_estudios_id,
                     'aprobadas_ids':sorted(aprobadas),'prerrequisitos_ids':sorted(p.pk for p in n.prerrequisitos.all()),
                     'cupo_grupo':elegido.cupo if elegido else None,
                     'grupo':elegido.clave if elegido else None,'profesor':elegido.profesor if elegido else None,
                     'horarios':elegido.horarios if elegido else [],
                     'explicacion':{'YA_APROBADA':'Materia ya acreditada.','PRERREQUISITOS':'Faltan prerrequisitos aprobados.',
                        'PLAN_INCORRECTO':'El plan no corresponde o está inactivo.','SIN_GRUPO':'No hay grupos ofrecidos.',
                        'SIN_CUPO':'Todos los grupos están llenos.','CONFLICTO_HORARIO':'Los grupos disponibles se cruzan con materias asignadas.'}.get(motivo,'Asignación válida según la política registrada.')}
            if elegido:
                usados[elegido.pk]+=1; horario.extend(elegido.horarios); counters['asignadas']+=1
            else: counters['pendientes']+=1
            resultados.append(ResultadoAsignacion(ejecucion=run,alumno=alumno,nodo=n,grupo=elegido,
                estado='ASIGNADA' if elegido else 'PENDIENTE',motivo=motivo,detalle=detalle))
    ResultadoAsignacion.objects.bulk_create(resultados)
    run.resumen={'alumnos':len(ordered),'asignadas':counters['asignadas'],'pendientes':counters['pendientes']}
    run.save(update_fields=['resumen','politica'])
    return run


@transaction.atomic
def publicar(run):
    Tenant.objects.select_for_update().get(pk=run.tenant_id)
    run=EjecucionAsignacion.objects.select_for_update().get(pk=run.pk)
    if run.estado=='ARCHIVADO': raise ReglaDeNegocioError('Una ejecución archivada no se vuelve a publicar; genera una nueva.')
    EjecucionAsignacion.objects.filter(tenant_id=run.tenant_id,estado='PUBLICADO').exclude(pk=run.pk).update(estado='ARCHIVADO')
    run.estado='PUBLICADO'; run.save(update_fields=['estado'])
    return run
