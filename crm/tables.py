import django_tables2 as tables
from .models import Cliente

class ClientiTable(tables.Table):
    nome = tables.Column(verbose_name="Nome", orderable=True)
    cognome = tables.Column(verbose_name="Cognome", orderable=True)
    email = tables.Column(verbose_name="Email")
    telefono = tables.Column(verbose_name="Telefono")
    residenza = tables.Column(verbose_name="Residenza")
    esperienza_finanziaria = tables.Column(verbose_name="Esperienza Finanziaria")
    visure = tables.Column(verbose_name="Visure")
    stato = tables.Column(verbose_name="Stato", attrs={"td": {"class": "td-nowrap"}})

    azioni = tables.TemplateColumn(
        template_code="""
        <div class="join justify-end">
          <a href="{% url 'cliente_dettaglio' record.pk %}" class="btn btn-ghost btn-sm join-item">Apri</a>
          <a href="{% url 'cliente_elimina' record.pk %}" class="btn btn-outline btn-sm join-item">Elimina</a>
        </div>
        """,
        orderable=False,
        verbose_name="Azioni",
        attrs={"th": {"class": "th-min td-actions"}, "td": {"class": "td-actions"}}
    )

    class Meta:
        model = Cliente
        fields = ("nome","cognome","email","telefono","residenza","esperienza_finanziaria","visure","stato")
        attrs = {"class": "table-app"}   # usa i nostri stili + DaisyUI
