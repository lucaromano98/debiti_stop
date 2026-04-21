from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0034_cliente_consulente"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="pratica",
            field=models.CharField(
                blank=True,
                choices=[
                    ("buon_fine", "Buon fine"),
                    ("doc_mancanti", "Doc Mancanti"),
                    ("revoca", "Revoca"),
                    ("cocluso", "Cocluso"),
                ],
                db_index=True,
                default="",
                max_length=20,
            ),
        ),
    ]
