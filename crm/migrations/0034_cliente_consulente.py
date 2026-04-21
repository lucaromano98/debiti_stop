from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0033_nota_lead"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="consulente",
            field=models.ForeignKey(
                blank=True,
                help_text="Consulente assegnato al cliente",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="clienti",
                to="crm.consulente",
            ),
        ),
    ]
