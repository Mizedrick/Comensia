import uuid
from django.db import models
from django.utils import timezone


class Servicio(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    duracion_minutos = models.PositiveIntegerField(default=60, help_text="Duración en minutos")
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Horario(models.Model):
    DIAS_SEMANA = [
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'),
        (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo'),
    ]

    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    capacidad_maxima = models.PositiveIntegerField(default=1, help_text="Reservas simultáneas permitidas")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"
        ordering = ['dia_semana', 'hora_inicio']
        unique_together = ['dia_semana', 'hora_inicio']

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_inicio:%H:%M}-{self.hora_fin:%H:%M}"


class FechaBloqueada(models.Model):
    fecha = models.DateField(unique=True)
    motivo = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Fecha Bloqueada"
        verbose_name_plural = "Fechas Bloqueadas"
        ordering = ['fecha']

    def __str__(self):
        return f"{self.fecha} - {self.motivo or 'Bloqueada'}"


class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.email})"

    def total_reservas(self):
        return self.reserva_set.count()


class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]

    codigo = models.CharField(max_length=12, unique=True, editable=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT)
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['fecha', 'hora']

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)

    def _generar_codigo(self):
        import random, string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Reserva.objects.filter(codigo=code).exists():
                return code

    def __str__(self):
        return f"#{self.codigo} - {self.cliente.nombre} | {self.fecha} {self.hora:%H:%M}"

    @property
    def puede_cancelar(self):
        from datetime import date, time, datetime
        ahora = timezone.localtime(timezone.now())
        reserva_dt = timezone.make_aware(
            timezone.datetime.combine(self.fecha, self.hora)
        )
        return self.estado in ('pendiente', 'confirmada') and reserva_dt > ahora
