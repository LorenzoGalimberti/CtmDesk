import django.db.models.deletion
from django.db import migrations, models


def sposta_clienti(apps, schema_editor):
    """Collega ogni procedura al cliente omonimo di core, creandolo se manca."""
    VecchioCliente = apps.get_model('procedura', 'Cliente')
    Procedura = apps.get_model('procedura', 'Procedura')
    ClienteCore = apps.get_model('core', 'Cliente')

    for vecchio in VecchioCliente.objects.all():
        nome = vecchio.nome.strip()
        nuovo = ClienteCore.objects.filter(nome__iexact=nome).first()
        if nuovo is None:
            nuovo = ClienteCore.objects.create(
                nome=nome, colore_sfondo='#6c757d', colore_testo='#ffffff'
            )
        Procedura.objects.filter(cliente=vecchio).update(cliente_core=nuovo)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('procedura', '0004_alter_step_options_step_ordine'),
    ]

    operations = [
        migrations.AddField(
            model_name='procedura',
            name='cliente_core',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.cliente',
            ),
        ),
        migrations.RunPython(sposta_clienti, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='procedura',
            name='cliente',
        ),
        migrations.RenameField(
            model_name='procedura',
            old_name='cliente_core',
            new_name='cliente',
        ),
        migrations.AlterField(
            model_name='procedura',
            name='cliente',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='core.cliente',
            ),
        ),
        migrations.DeleteModel(
            name='Cliente',
        ),
    ]
