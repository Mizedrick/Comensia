from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from reservations.models import Servicio, Horario, Cliente, Reserva
from datetime import time, date, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Carga datos de demostración'

    def handle(self, *args, **kwargs):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@comensia.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Admin creado: admin / admin123'))

        services_data = [
            ('Mesa para 2 personas', 'Mesa íntima para cenas especiales.', 60, 0),
            ('Mesa para 4 personas', 'Mesa familiar para compartir.', 90, 0),
            ('Mesa para 6 personas', 'Mesa grupal para celebraciones.', 120, 0),
            ('Evento Privado', 'Reserva del salón privado.', 180, 500000),
        ]
        for nombre, desc, dur, precio in services_data:
            s, created = Servicio.objects.get_or_create(
                nombre=nombre, defaults={'descripcion': desc, 'duracion_minutos': dur, 'precio': precio}
            )
            if created:
                self.stdout.write(f'  Servicio: {nombre}')

        for dia in range(6):
            for hora_ini, hora_fin, cap in [(time(12,0), time(14,0), 8), (time(19,0), time(22,0), 10)]:
                Horario.objects.get_or_create(
                    dia_semana=dia, hora_inicio=hora_ini,
                    defaults={'hora_fin': hora_fin, 'capacidad_maxima': cap}
                )

        # Demo bookings
        hoy = timezone.localdate()
        clientes_demo = [
            ('María García', '+57 310 123 4567', 'maria@demo.com'),
            ('Carlos López', '+57 320 234 5678', 'carlos@demo.com'),
            ('Ana Martínez', '+57 300 345 6789', 'ana@demo.com'),
        ]
        servicio = Servicio.objects.first()
        for nombre, tel, email in clientes_demo:
            cliente, _ = Cliente.objects.get_or_create(email=email, defaults={'nombre': nombre, 'telefono': tel})
            Reserva.objects.get_or_create(
                cliente=cliente, fecha=hoy + timedelta(days=1),
                hora=time(12, 0), servicio=servicio,
                defaults={'estado': 'pendiente'}
            )

        self.stdout.write(self.style.SUCCESS('¡Datos demo cargados correctamente!'))
