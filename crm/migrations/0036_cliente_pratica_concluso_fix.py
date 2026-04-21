from django.db import migrations, models


def migra_pratica_cocluso_to_concluso(apps, schema_editor):
    Cliente = apps.get_model("crm", "Cliente")
    Cliente.objects.filter(pratica="cocluso").update(pratica="concluso")


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0035_cliente_pratica"),
    ]

    operations = [
        migrations.RunPython(migra_pratica_cocluso_to_concluso, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="cliente",
            name="pratica",
            field=models.CharField(
                blank=True,
                choices=[
                    ("buon_fine", "Buon fine"),
                    ("doc_mancanti", "Doc Mancanti"),
                    ("revoca", "Revoca"),
                    ("concluso", "Concluso"),
                ],
                db_index=True,
                default="",
                max_length=20,
            ),
        ),
    ]
