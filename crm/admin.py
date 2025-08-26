from django.contrib import admin

# Register your models here.

from .models import Cliente, Pratiche, ProfiloUtente

admin.site.register(Cliente)
admin.site.register(Pratiche)
admin.site.register(ProfiloUtente)