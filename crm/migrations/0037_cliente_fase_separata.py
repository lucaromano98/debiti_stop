from django.db import migrations, models


def migra_stato_in_fase(apps, schema_editor):
    Cliente = apps.get_model("crm", "Cliente")

    Cliente.objects.filter(stato="legal").update(stato="active", fase="legale")
    Cliente.objects.filter(stato="stragiudiziale").update(stato="active", fase="stragiudiziale")
    Cliente.objects.filter(stato="istanza").update(stato="active", fase="istanza")


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0036_cliente_pratica_concluso_fix"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="fase",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Nessuna"),
                    ("legale", "Legale"),
                    ("stragiudiziale", "Stragiudiziale"),
                    ("istanza", "Istanza di visibilità"),
                ],
                db_index=True,
                default="",
                max_length=20,
            ),
        ),
        migrations.RunPython(migra_stato_in_fase, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="cliente",
            name="stato",
            field=models.CharField(
                choices=[("active", "Attivo"), ("inactive", "Non Attivo")],
                db_index=True,
                default="active",
                max_length=50,
            ),
        ),
    ]
