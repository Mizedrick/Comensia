from django.contrib import admin
from .models import Servicio, Horario, FechaBloqueada, Cliente, Reserva


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'duracion_minutos', 'precio', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ['get_dia_semana_display', 'hora_inicio', 'hora_fin', 'capacidad_maxima', 'activo']
    list_filter = ['activo', 'dia_semana']


@admin.register(FechaBloqueada)
class FechaBloqueadaAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'motivo']
    ordering = ['fecha']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'email', 'telefono', 'created_at']
    search_fields = ['nombre', 'email']


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'cliente', 'servicio', 'fecha', 'hora', 'estado', 'created_at']
    list_filter = ['estado', 'servicio', 'fecha']
    search_fields = ['codigo', 'cliente__nombre', 'cliente__email']
    readonly_fields = ['codigo', 'created_at', 'updated_at']
