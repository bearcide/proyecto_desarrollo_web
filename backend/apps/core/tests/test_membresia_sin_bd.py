"""Pruebas sin conexión a bases; ejecutar con settings mínimos y unittest."""
from importlib import import_module
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from django.db import models
from django.db.migrations.state import ProjectState
from apps.core.models import MembresiaTenant

poblacion = import_module('apps.core.migrations.0003_poblar_membresias_alumnos')


class MembresiaSinBaseTests(TestCase):
    def test_restriccion_y_defaults(self):
        meta = MembresiaTenant._meta
        constraint, = meta.constraints
        self.assertEqual(constraint.fields, ('user', 'tenant'))
        self.assertEqual(constraint.name, 'uq_membresia_user_tenant')
        self.assertTrue(meta.get_field('activo').default)
        self.assertFalse(meta.get_field('es_alumno').default)
        self.assertFalse(meta.get_field('es_administrador').default)
        for name in ('user', 'tenant'):
            field = meta.get_field(name)
            self.assertFalse(field.null)
            self.assertIs(field.remote_field.on_delete, models.PROTECT)

    def test_estado_migraciones_coincide_con_modelos(self):
        from django.apps import apps
        state = ProjectState()
        for name in ('0001_initial', '0002_membresia_tenant', '0003_poblar_membresias_alumnos', '0004_demo_academica'):
            migration = import_module('apps.core.migrations.' + name).Migration(name, 'core')
            state = migration.mutate_state(state)
        current = ProjectState.from_apps(apps)
        for key, expected in current.models.items():
            if key[0] == 'core':
                self.assertEqual(state.models[key], expected, key)

    def test_poblacion_usa_historicos_alias_y_no_sobrescribe(self):
        alumnos, membresias = Mock(), Mock()
        apps = Mock()
        apps.get_model.side_effect = lambda app, name: {'Alumno': alumnos, 'MembresiaTenant': membresias}[name]
        query = alumnos.objects.using.return_value.filter.return_value.order_by.return_value.values_list.return_value.distinct.return_value
        query.iterator.return_value = iter([(11, 'escuela-a'), (11, 'escuela-b')])
        manager = membresias.objects.using.return_value
        poblacion.poblar_membresias_alumnos(apps, SimpleNamespace(connection=SimpleNamespace(alias='aislada')))
        alumnos.objects.using.assert_called_once_with('aislada')
        alumnos.objects.using.return_value.filter.assert_called_once_with(user_id__isnull=False)
        alumnos.objects.using.return_value.filter.return_value.order_by.assert_called_once_with()
        membresias.objects.using.assert_called_once_with('aislada')
        self.assertEqual(manager.get_or_create.call_count, 2)
        for call in manager.get_or_create.call_args_list:
            self.assertEqual(call.kwargs['defaults'], {'activo': True, 'es_alumno': True, 'es_administrador': False})
        manager.update.assert_not_called()
        manager.update_or_create.assert_not_called()
        alumnos.objects.update.assert_not_called()

    def test_reversion_no_elimina_datos(self):
        from django.db.migrations import RunPython
        operation, = poblacion.Migration.operations
        self.assertIs(operation.reverse_code, RunPython.noop)
