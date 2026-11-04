from django.db import migrations


def poblar_membresias_alumnos(apps, schema_editor):
    """Solo crea asociaciones faltantes; no reactiva ni cambia roles existentes.

    No busca usuarios por matrícula y no altera expedientes académicos.
    El estado de usuario, alumno y escuela deberá validarse al autorizar acceso.
    """
    Alumno = apps.get_model('core', 'Alumno')
    MembresiaTenant = apps.get_model('core', 'MembresiaTenant')
    alias = schema_editor.connection.alias
    pares = (
        Alumno.objects.using(alias)
        .filter(user_id__isnull=False)
        .order_by()
        .values_list('user_id', 'tenant_id')
        .distinct()
    )
    membresias = MembresiaTenant.objects.using(alias)
    for user_id, tenant_id in pares.iterator(chunk_size=1000):
        membresias.get_or_create(
            user_id=user_id, tenant_id=tenant_id,
            defaults={
                'activo': True,
                'es_alumno': True,
                'es_administrador': False,
            },
        )


class Migration(migrations.Migration):
    dependencies = [('core', '0002_membresia_tenant')]

    # Reversión intencionalmente no destructiva: conserva membresías y roles
    # que podrían haber cambiado después de la población inicial.
    operations = [
        migrations.RunPython(poblar_membresias_alumnos, migrations.RunPython.noop),
    ]
