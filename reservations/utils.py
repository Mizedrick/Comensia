from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def enviar_confirmacion_reserva(reserva):
    """Envía email de confirmación al cliente."""
    subject = f"Confirmación de reserva #{reserva.codigo} - {settings.BUSINESS_NAME}"
    message = f"""
Hola {reserva.cliente.nombre},

Tu reserva ha sido recibida exitosamente.

Detalles:
- Código: {reserva.codigo}
- Servicio: {reserva.servicio.nombre}
- Fecha: {reserva.fecha.strftime('%d/%m/%Y')}
- Hora: {reserva.hora.strftime('%H:%M')}
- Estado: {reserva.get_estado_display()}

Puedes consultar o cancelar tu reserva en:
http://localhost:8000/mi-reserva/

¡Te esperamos!
{settings.BUSINESS_NAME}
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [reserva.cliente.email])
    except Exception as e:
        print(f"Error enviando email: {e}")


def get_horas_disponibles(fecha, servicio=None):
    """Retorna lista de horas disponibles para una fecha dada."""
    from .models import Horario, Reserva, FechaBloqueada
    from django.utils import timezone

    if FechaBloqueada.objects.filter(fecha=fecha).exists():
        return []

    dia_semana = fecha.weekday()
    horarios = Horario.objects.filter(dia_semana=dia_semana, activo=True)
    disponibles = []

    for horario in horarios:
        reservas_count = Reserva.objects.filter(
            fecha=fecha,
            hora=horario.hora_inicio,
            estado__in=['pendiente', 'confirmada']
        ).count()
        if reservas_count < horario.capacidad_maxima:
            disponibles.append({
                'hora': horario.hora_inicio,
                'hora_str': horario.hora_inicio.strftime('%H:%M'),
                'disponibles': horario.capacidad_maxima - reservas_count,
            })

    return disponibles
