# Generated manually for stato operativo "Non fascia oraria"

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0031_alter_lead_stato_operativo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lead",
            name="stato_operativo",
            field=models.CharField(
                choices=[
                    ("nuovo", "Nuovo"),
                    ("no_risposta", "Senza risposta"),
                    ("segreteria", "Segreteria"),
                    ("non_fascia_oraria", "Non fascia oraria"),
                    ("ha_staccato_lui", "Ha staccato lui"),
                    ("consulenza_eff", "Consulenza effettuata"),
                    ("attesa_contatti", "Attesa contatti cliente"),
                    ("non_contattare", "Non contattare"),
                    ("numero_errato", "Numero errato"),
                    ("blocco_chiamate", "Blocco chiamate"),
                    ("cliente_non_interessato", "Cliente non interessato"),
                    ("non_competenza", "Attività non di competenza"),
                ],
                db_index=True,
                default="nuovo",
                max_length=30,
            ),
        ),
    ]
