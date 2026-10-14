import django.db.models.deletion
from django.db import migrations, models


def sposta_clienti(apps, schema_editor):
    """Collega ogni errore al cliente omonimo di core, creandolo se manca."""
    VecchioCliente = apps.get_model('errors', 'Cliente')
    Errore = apps.get_model('errors', 'Errore')
    ClienteCore = apps.get_model('core', 'Cliente')

    for vecchio in VecchioCliente.objects.all():
        nome = vecchio.nome.strip()
        nuovo = ClienteCore.objects.filter(nome__iexact=nome).first()
        if nuovo is None:
            nuovo = ClienteCore.objects.create(
                nome=nome, colore_sfondo='#6c757d', colore_testo='#ffffff'
            )
        Errore.objects.filter(cliente=vecchio).update(cliente_core=nuovo)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('errors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='errore',
            name='cliente_core',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.cliente',
            ),
        ),
        migrations.RunPython(sposta_clienti, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='errore',
            name='cliente',
        ),
        migrations.RenameField(
            model_name='errore',
            old_name='cliente_core',
            new_name='cliente',
        ),
        migrations.AlterField(
            model_name='errore',
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
