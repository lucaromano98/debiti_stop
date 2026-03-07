# Generated manually

from django.db import migrations, models


def migra_stati_operativi(apps, schema_editor):
    """Converte msg_inviato -> no_risposta, in_acquisizione -> attesa_contatti"""
    Lead = apps.get_model("crm", "Lead")
    Lead.objects.filter(stato_operativo="msg_inviato").update(stato_operativo="no_risposta")
    Lead.objects.filter(stato_operativo="in_acquisizione").update(stato_operativo="attesa_contatti")


def reverse_migra(apps, schema_editor):
    pass  # non reversibile in modo sicuro


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0029_lead_creditore_legale_lead_creditore_legale_altro"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="ricontatti_count",
            field=models.PositiveIntegerField(default=0, help_text="Numero di ricontatti senza risposta"),
        ),
        migrations.RunPython(migra_stati_operativi, reverse_migra),
        migrations.AlterField(
            model_name="lead",
            name="stato_operativo",
            field=models.CharField(
                choices=[
                    ("nuovo", "Nuovo"),
                    ("no_risposta", "Senza risposta"),
                    ("segreteria", "Segreteria"),
                    ("ha_staccato_lui", "Ha staccato lui"),
                    ("consulenza_eff", "Consulenza effettuata"),
                    ("non_competenza", "Attività non di competenza"),
                    ("attesa_contatti", "Attesa contatti cliente"),
                    ("non_contattare", "Non contattare"),
                ],
                db_index=True,
                default="nuovo",
                max_length=30,
            ),
        ),
    ]
