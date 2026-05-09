from django.urls import path
from . import views

urlpatterns = [
    # Públicas
    path('', views.inicio, name='inicio'),
    path('reservar/', views.reservar, name='reservar'),
    path('reservar/confirmada/<str:codigo>/', views.reserva_confirmada, name='reserva_confirmada'),
    path('mi-reserva/', views.mi_reserva, name='mi_reserva'),
    path('mi-reserva/cancelar/<str:codigo>/', views.cancelar_reserva_publica, name='cancelar_reserva_publica'),
    path('api/horas-disponibles/', views.horas_disponibles_api, name='horas_disponibles_api'),

    # Admin panel
    path('admin-panel/', views.dashboard, name='dashboard'),
    path('admin-panel/reservas/', views.admin_reservas, name='admin_reservas'),
    path('admin-panel/reservas/<int:pk>/', views.admin_reserva_detalle, name='admin_reserva_detalle'),
    path('admin-panel/reservas/<int:pk>/accion/', views.admin_reserva_accion, name='admin_reserva_accion'),

    path('admin-panel/servicios/', views.admin_servicios, name='admin_servicios'),
    path('admin-panel/servicios/nuevo/', views.admin_servicio_crear, name='admin_servicio_crear'),
    path('admin-panel/servicios/<int:pk>/editar/', views.admin_servicio_editar, name='admin_servicio_editar'),
    path('admin-panel/servicios/<int:pk>/eliminar/', views.admin_servicio_eliminar, name='admin_servicio_eliminar'),

    path('admin-panel/horarios/', views.admin_horarios, name='admin_horarios'),
    path('admin-panel/horarios/crear/', views.admin_horario_crear, name='admin_horario_crear'),
    path('admin-panel/horarios/<int:pk>/eliminar/', views.admin_horario_eliminar, name='admin_horario_eliminar'),
    path('admin-panel/horarios/bloquear/', views.admin_fecha_bloquear, name='admin_fecha_bloquear'),
    path('admin-panel/horarios/desbloquear/<int:pk>/', views.admin_fecha_desbloquear, name='admin_fecha_desbloquear'),

    path('admin-panel/clientes/', views.admin_clientes, name='admin_clientes'),
    path('admin-panel/clientes/<int:pk>/', views.admin_cliente_detalle, name='admin_cliente_detalle'),

    path('admin-panel/reportes/', views.admin_reportes, name='admin_reportes'),
]
