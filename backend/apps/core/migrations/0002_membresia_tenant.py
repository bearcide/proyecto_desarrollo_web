from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MembresiaTenant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activo', models.BooleanField(default=True)),
                ('es_alumno', models.BooleanField(default=False)),
                ('es_administrador', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='membresias_tenant', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='membresias', to='core.tenant')),
            ],
            options={
                'verbose_name': 'membresía de escuela',
                'verbose_name_plural': 'membresías de escuelas',
                'constraints': [models.UniqueConstraint(fields=('user', 'tenant'), name='uq_membresia_user_tenant')],
            },
        ),
    ]
