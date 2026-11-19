from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0004_demo_academica')]
    operations = [
        # Solo las filas preexistentes conservan transición; altas nuevas son estrictas.
        migrations.AddField(
            model_name='tenant', name='licencia_requerida',
            field=models.BooleanField(default=False, editable=False), preserve_default=False,
        ),
        migrations.AlterField(
            model_name='tenant', name='licencia_requerida',
            field=models.BooleanField(default=True, editable=False),
        ),
    ]
