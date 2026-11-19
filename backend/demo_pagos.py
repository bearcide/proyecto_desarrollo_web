"""Crea una base NUEVA, migra y siembra; --verificar ejecuta el recorrido por JWT."""
import argparse
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--verificar', action='store_true')
    args = parser.parse_args()
    path = Path(args.database)
    base = Path(__file__).resolve().parent
    if not path.is_absolute() or path.parent.resolve() != base or path.is_symlink() or not path.name.startswith('demo_pagos_') or path.suffix != '.sqlite3':
        parser.error('Usa una ruta absoluta backend/demo_pagos_*.sqlite3 nueva.')
    # Exclusión antes de Django: jamás abrir/sobrescribir una base existente.
    with path.open('xb'):
        pass
    os.environ['PAGOS_DEMO_DATABASE'] = str(path)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_pagos_demo'
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import transaction
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from datetime import timedelta
    from apps.core.models import Tenant, MembresiaTenant
    from apps.comercial import models as m, services as s
    from apps.core.services.identidad import ErrorIdentidad
    from rest_framework.test import APIClient

    call_command('migrate', interactive=False)
    call_command('migrate', check=True)
    call_command('check')
    ident = lambda name: uuid5(NAMESPACE_URL, 'ime:pagos-demo:' + name)
    with transaction.atomic():
        a = Tenant.objects.create(id=ident('a'), nombre_comercial='Instituto Horizonte Ficticio', plan_suscripcion='demo')
        b = Tenant.objects.create(id=ident('b'), nombre_comercial='Academia Alterna Ficticia', plan_suscripcion='demo')
        users = {}
        for name in ('propietario_demo', 'admin_demo', 'admin_otro_demo', 'staff_demo'):
            users[name] = get_user_model().objects.create_user(username=name, password='Demo-Pagos-2026!', is_superuser=name=='propietario_demo', is_staff=name in ('propietario_demo', 'staff_demo'))
        for name, tenant in [('admin_demo', a), ('admin_otro_demo', b), ('staff_demo', a)]:
            MembresiaTenant.objects.create(user=users[name], tenant=tenant, es_administrador=True)
        # Vue requiere membresía incluso al propietario; no concede rol académico.
        MembresiaTenant.objects.create(user=users['propietario_demo'], tenant=a)
        plan = m.Plan.objects.create(id=ident('plan'), codigo='demo-horizonte', nombre='Horizonte DEMO', funcionalidades={'alumnos': True, 'planes_estudios': True, 'horarios': True, 'reportes': True, 'asignaciones': True, 'importaciones': True}, max_alumnos=100, max_planteles=2)
        price = m.Precio.objects.create(id=ident('monthly'), plan=plan, modalidad='monthly', importe='100.00', por_alumno='2.50', dias=30)
        enterprise = m.Precio.objects.create(id=ident('enterprise'), plan=plan, modalidad='enterprise', importe='1200.00', dias=365)
        basic = m.Plan.objects.create(id=ident('plan-basico'), codigo='demo-basico', nombre='Básico DEMO', funcionalidades={'alumnos': True, 'planes_estudios': True, 'horarios': True}, max_alumnos=30, max_planteles=1)
        m.Precio.objects.create(id=ident('process'), plan=basic, modalidad='process', importe='50.00', dias=30)
        contract = m.Contrato.objects.create(id=ident('contrato'), tenant=a, precio=enterprise, inicio=timezone.now()-timedelta(days=1), fin=timezone.now()+timedelta(days=365), estado='draft', condiciones='Ficticio; aprobación exclusiva del propietario.')
        from apps.core.models import PlanEstudios, Nodo, Grupo, Alumno, SolicitudMateria
        academic = PlanEstudios.objects.create(tenant=a, nombre='Ingeniería ficticia')
        node = Nodo.objects.create(tenant=a, plan_estudios=academic, clave='DEMO-MAT', nombre='Matemáticas ficticias', creditos=4, semestre=1)
        Grupo.objects.create(tenant=a, nodo=node, clave='DEMO-G1', profesor='Docente ficticio', cupo=30,
                             horarios=[{'dia':'Lunes', 'inicio':480, 'fin':600}])
        student_user = get_user_model().objects.create_user(username='alumno_pagos_demo', password='Demo-Pagos-2026!')
        MembresiaTenant.objects.create(user=student_user, tenant=a, es_alumno=True)
        student = Alumno.objects.create(tenant=a, plan_estudios=academic, user=student_user,
                                       numero_de_cuenta='alumno_pagos_demo', nombre='Estudiante ficticio', apellido_paterno='Pagos')
        SolicitudMateria.objects.create(tenant=a, alumno=student, nodo=node)
    print(f'BASE={path}\nTENANT={a.id}\nPRECIO_MENSUAL={price.id}\nPRECIO_EMPRESA={enterprise.id}\nCONTRATO={contract.id}')
    print('Usuarios: propietario_demo, admin_demo, admin_otro_demo, staff_demo, alumno_pagos_demo; contraseña local: Demo-Pagos-2026!')
    if not args.verificar:
        return

    prefix = '/api/v1/comercial/'
    def expect(response, status):
        if response.status_code != status:
            raise AssertionError((response.status_code, status, getattr(response, 'data', None)))
        return response.data
    def login(name):
        client = APIClient()
        pair = expect(client.post('/api/v1/token/', {'matricula': name, 'password': 'Demo-Pagos-2026!'}, format='json'), 200)
        expect(client.post('/api/v1/token/refresh/', {'refresh': pair['refresh']}, format='json'), 200)
        client.credentials(HTTP_AUTHORIZATION='Bearer '+pair['access'])
        return client
    admin, owner, other, staff = [login(n) for n in ('admin_demo','propietario_demo','admin_otro_demo','staff_demo')]
    expect(APIClient().get(prefix+'ordenes/'), 401)
    bad = APIClient(); bad.credentials(HTTP_AUTHORIZATION='Bearer invalido')
    expect(bad.get(prefix+'ordenes/'), 401)
    assert not expect(admin.get(prefix+'acceso/'), 200)['activo']
    expect(admin.get('/api/v1/alumnos/'), 403)
    expect(admin.get('/api/v1/demo/grupos/'), 403)
    data = {'precio': str(enterprise.id), 'contrato': str(contract.id), 'alumnos': 2}
    headers = {'HTTP_IDEMPOTENCY_KEY': 'demo_empresa_0001'}
    expect(admin.post(prefix+'checkout/', data, format='json', **headers), 400)
    url = prefix+f'contratos/{contract.id}/'
    expect(admin.patch(url, {'estado':'active'}, format='json'), 403)
    expect(staff.patch(url, {'estado':'active'}, format='json'), 403)
    expect(owner.patch(url, {'estado':'active'}, format='json'), 200)
    order = expect(admin.post(prefix+'checkout/', data, format='json', **headers), 201)
    assert order['proveedor'] == 'DEMO' and order['url'] is None and order['estado'] == 'pending'
    assert expect(admin.post(prefix+'checkout/', data, format='json', **headers), 201)['orden'] == order['orden']
    expect(admin.post(prefix+'checkout/', {**data, 'alumnos':3}, format='json', **headers), 409)
    expect(admin.post(prefix+'checkout/', {**data, 'importe':'0.01'}, format='json', **headers), 400)
    assert not expect(admin.get(prefix+'acceso/'), 200)['activo']
    confirmation = {'orden':order['orden'], 'resultado':'paid', 'referencia':'demo_empresa_pago_0001'}
    for client in (admin, staff, other):
        expect(client.post(prefix+'demo/confirmar/', confirmation, format='json'), 403)
    for _ in range(2):
        expect(owner.post(prefix+'demo/confirmar/', confirmation, format='json'), 200)
    obj = m.Orden.objects.get(pk=order['orden'])
    assert obj.estado == 'paid' and str(obj.importe) == '1200.00'
    assert m.Transaccion.objects.filter(orden=obj).count() == m.Comprobante.objects.count() == m.Licencia.objects.count() == 1
    assert expect(admin.get(prefix+'acceso/'), 200)['funcionalidades']['horarios']
    for resource, instance in [('ordenes',obj), ('licencias',obj.licencia), ('transacciones',obj.transaccion_set.get()), ('comprobantes',m.Comprobante.objects.get()), ('contratos',contract)]:
        expect(other.get(prefix+f'{resource}/{instance.pk}/'), 404)
        assert expect(other.get(prefix+resource+'/'), 200)['count'] == 0
    expect(admin.get(prefix+'ordenes/', HTTP_X_TENANT_ID=str(b.id)), 403)
    assert not expect(other.get(prefix+'acceso/'), 200)['activo']
    s.exigir_capacidad(a, funcionalidad='horarios', alumnos=100, planteles=2)
    for kwargs in ({'funcionalidad':'no_contratada'}, {'alumnos':101}, {'planteles':3}):
        try:
            s.exigir_capacidad(a, **kwargs)
        except ErrorIdentidad:
            pass
        else:
            raise AssertionError('Límite/funcionalidad no rechazado')
    pdf = admin.get(prefix+f'comprobantes/{m.Comprobante.objects.get().pk}/pdf/')
    assert pdf.status_code == 200 and pdf.content.startswith(b'%PDF')
    # Segundo recorrido recurrente: misma clave en otro tenant es independiente.
    monthly = {'precio':str(price.id), 'alumnos':2}
    recurring = expect(admin.post(prefix+'checkout/', monthly, format='json', HTTP_IDEMPOTENCY_KEY='demo_mensual_0001'), 201)
    expect(other.post(prefix+'checkout/', monthly, format='json', HTTP_IDEMPOTENCY_KEY='demo_mensual_0001'), 201)
    expect(owner.post(prefix+'demo/confirmar/', {'orden':recurring['orden'], 'resultado':'paid', 'referencia':'demo_mensual_pago_0001'}, format='json'), 200)
    assert m.Suscripcion.objects.get().estado == 'active'
    assert str(m.Orden.objects.get(pk=recurring['orden']).importe) == '105.00'
    expect(admin.get(prefix+'ingresos/'), 403)
    print('INGRESOS=', expect(owner.get(prefix+'ingresos/'), 200))
    print('OK: JWT/refresh, 401/403/404/409, contrato aprobado por propietario, pago DEMO exclusivo, aislamiento, idempotencia, licencia, capacidades, PDF y suscripción.')
    # Plan básico independiente: habilita horarios y bloquea reportes en Django.
    basic_order = expect(other.post(prefix+'checkout/', {'precio':str(ident('process')), 'alumnos':1}, format='json', HTTP_IDEMPOTENCY_KEY='demo_basico_0001'), 201)
    expect(owner.post(prefix+'demo/confirmar/', {'orden':basic_order['orden'], 'resultado':'paid', 'referencia':'demo_basico_pago_0001'}, format='json'), 200)
    expect(other.get('/api/v1/demo/grupos/'), 200)
    denied = expect(other.get('/api/v1/demo/estadisticas/'), 403)
    assert denied['code'] == 'license_required'
    expect(admin.get('/api/v1/alumnos/'), 200)
    expect(admin.post('/api/v1/demo/asignaciones/generar/', {}, format='json'), 201)
    print('OK académico: plan básico permite grupos y rechaza reportes; Horizonte permite alumnos y genera asignación real.')
    print('INGRESOS FINALES=', expect(owner.get(prefix+'ingresos/'), 200))


if __name__ == '__main__':
    main()
