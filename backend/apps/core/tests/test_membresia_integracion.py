"""Requiere base de pruebas migrada. NO ejecutar durante la Fase 1 sin permiso."""
from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.core.models import Alumno, MembresiaTenant, PlanEstudios, Tenant

poblar = import_module('apps.core.migrations.0003_poblar_membresias_alumnos').poblar_membresias_alumnos


class MembresiaIntegracionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alumno-existente')
        self.tenant = Tenant.objects.create(nombre_comercial='A', plan_suscripcion='prueba')
        self.plan = PlanEstudios.objects.create(tenant=self.tenant, nombre='Plan')
        self.alumno = Alumno.objects.create(
            tenant=self.tenant, plan_estudios=self.plan, user=self.user,
            nombre='Alumno', apellido_paterno='Existente', numero_de_cuenta='00042',
            promedio_acumulado=9.1, materias_aprobadas_ids=[3, 7],
        )

    def poblar(self):
        poblar(apps, SimpleNamespace(connection=connection))

    def test_unicidad_y_usuario_multiescuela(self):
        MembresiaTenant.objects.create(user=self.user, tenant=self.tenant)
        with self.assertRaises(IntegrityError), transaction.atomic():
            MembresiaTenant.objects.create(user=self.user, tenant=self.tenant)
        otra = Tenant.objects.create(nombre_comercial='B', plan_suscripcion='prueba')
        MembresiaTenant.objects.create(user=self.user, tenant=otra)
        self.assertEqual(MembresiaTenant.objects.count(), 2)

    def test_relaciones_obligatorias_y_protegidas(self):
        for attrs in ({'tenant': self.tenant}, {'user': self.user}):
            with self.assertRaises(IntegrityError), transaction.atomic():
                MembresiaTenant.objects.create(**attrs)
        MembresiaTenant.objects.create(user=self.user, tenant=self.tenant)
        with self.assertRaises(ProtectedError):
            self.user.delete()
        with self.assertRaises(ProtectedError):
            self.tenant.delete()

    def test_poblacion_idempotente_preserva_todos_los_datos(self):
        antes = list(Alumno.objects.order_by('pk').values())
        usuarios = list(get_user_model().objects.order_by('pk').values())
        self.poblar()
        self.poblar()
        membership = MembresiaTenant.objects.get(user=self.user, tenant=self.tenant)
        self.assertTrue(membership.es_alumno)
        self.assertFalse(membership.es_administrador)
        self.assertEqual(MembresiaTenant.objects.count(), 1)
        self.assertEqual(antes, list(Alumno.objects.order_by('pk').values()))
        self.assertEqual(usuarios, list(get_user_model().objects.order_by('pk').values()))

    def test_preserva_membresia_inactiva_y_roles_existentes(self):
        membership = MembresiaTenant.objects.create(
            user=self.user, tenant=self.tenant, activo=False,
            es_alumno=False, es_administrador=True,
        )
        antes = MembresiaTenant.objects.values().get(pk=membership.pk)
        self.poblar()
        self.assertEqual(antes, MembresiaTenant.objects.values().get(pk=membership.pk))

    def test_sin_usuario_y_perfiles_duplicados(self):
        Alumno.objects.create(tenant=self.tenant, plan_estudios=self.plan, nombre='Sin usuario', apellido_paterno='Existente')
        Alumno.objects.create(tenant=self.tenant, plan_estudios=self.plan, user=self.user, nombre='Duplicado', apellido_paterno='Existente')
        self.poblar()
        self.assertEqual(Alumno.objects.count(), 3)
        self.assertEqual(MembresiaTenant.objects.count(), 1)

    def test_staff_superuser_no_generan_administracion(self):
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.poblar()
        self.assertFalse(MembresiaTenant.objects.get(user=self.user, tenant=self.tenant).es_administrador)
