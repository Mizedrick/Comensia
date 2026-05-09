from django import forms
from django.utils import timezone
from .models import Reserva, Cliente, Servicio, Horario, FechaBloqueada
import datetime


class ReservaPublicaForm(forms.Form):
    servicio = forms.ModelChoiceField(
        queryset=Servicio.objects.filter(activo=True),
        label="Servicio",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_servicio'})
    )
    fecha = forms.DateField(
        label="Fecha",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_fecha'})
    )
    hora = forms.ChoiceField(
        label="Hora disponible",
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_hora'})
    )
    nombre = forms.CharField(
        max_length=200, label="Nombre completo",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre completo'})
    )
    telefono = forms.CharField(
        max_length=20, label="Teléfono",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+57 300 000 0000'})
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'})
    )
    notas = forms.CharField(
        required=False, label="Notas adicionales",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Cualquier información adicional...'})
    )

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        hoy = timezone.localdate()
        if fecha < hoy:
            raise forms.ValidationError("La fecha no puede ser en el pasado.")
        if FechaBloqueada.objects.filter(fecha=fecha).exists():
            raise forms.ValidationError("Esta fecha no está disponible.")
        return fecha

    def clean(self):
        cleaned = super().clean()
        fecha = cleaned.get('fecha')
        hora_str = cleaned.get('hora')
        servicio = cleaned.get('servicio')

        if fecha and hora_str and servicio:
            try:
                hora = datetime.time.fromisoformat(hora_str)
            except (ValueError, TypeError):
                raise forms.ValidationError("Hora inválida.")

            dia_semana = fecha.weekday()
            horario = Horario.objects.filter(
                dia_semana=dia_semana,
                hora_inicio=hora,
                activo=True
            ).first()

            if not horario:
                raise forms.ValidationError("El horario seleccionado no está disponible.")

            reservas_existentes = Reserva.objects.filter(
                fecha=fecha, hora=hora,
                estado__in=['pendiente', 'confirmada']
            ).count()

            if reservas_existentes >= horario.capacidad_maxima:
                raise forms.ValidationError("No hay disponibilidad en ese horario. Por favor elige otro.")

        return cleaned


class BuscarReservaForm(forms.Form):
    busqueda = forms.CharField(
        max_length=200,
        label="Código de reserva o correo electrónico",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ej: ABC12345 o tu@correo.com'
        })
    )


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'duracion_minutos', 'precio', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duracion_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['dia_semana', 'hora_inicio', 'hora_fin', 'capacidad_maxima', 'activo']
        widgets = {
            'dia_semana': forms.Select(attrs={'class': 'form-select'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'capacidad_maxima': forms.NumberInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FechaBloqueadaForm(forms.ModelForm):
    class Meta:
        model = FechaBloqueada
        fields = ['fecha', 'motivo']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Festivo, Vacaciones...'}),
        }


class FiltroReservasForm(forms.Form):
    ESTADO_CHOICES = [('', 'Todos')] + list(Reserva.ESTADO_CHOICES)

    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    estado = forms.ChoiceField(
        required=False, choices=ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    servicio = forms.ModelChoiceField(
        required=False,
        queryset=Servicio.objects.all(),
        empty_label="Todos los servicios",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
