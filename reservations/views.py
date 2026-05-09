import json
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Servicio, Horario, Cliente, Reserva, FechaBloqueada
from .forms import (
    ReservaPublicaForm, BuscarReservaForm, ServicioForm,
    HorarioForm, FechaBloqueadaForm, FiltroReservasForm
)
from .utils import enviar_confirmacion_reserva, get_horas_disponibles


# ─── VISTAS PÚBLICAS ───────────────────────────────────────────────────────────

def inicio(request):
    servicios = Servicio.objects.filter(activo=True)
    return render(request, 'public/inicio.html', {'servicios': servicios})


def reservar(request):
    if request.method == 'POST':
        form = ReservaPublicaForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            hora = datetime.time.fromisoformat(data['hora'])

            cliente, _ = Cliente.objects.get_or_create(
                email=data['email'],
                defaults={'nombre': data['nombre'], 'telefono': data['telefono']}
            )
            # Actualizar datos si ya existe
            cliente.nombre = data['nombre']
            cliente.telefono = data['telefono']
            cliente.save()

            reserva = Reserva.objects.create(
                cliente=cliente,
                servicio=data['servicio'],
                fecha=data['fecha'],
                hora=hora,
                notas=data.get('notas', ''),
            )
            enviar_confirmacion_reserva(reserva)
            return redirect('reserva_confirmada', codigo=reserva.codigo)
    else:
        form = ReservaPublicaForm()

    servicios = Servicio.objects.filter(activo=True)
    return render(request, 'public/reservar.html', {'form': form, 'servicios': servicios})


def reserva_confirmada(request, codigo):
    reserva = get_object_or_404(Reserva, codigo=codigo)
    return render(request, 'public/reserva_confirmada.html', {'reserva': reserva})


def mi_reserva(request):
    reservas = []
    form = BuscarReservaForm()

    if request.method == 'POST':
        form = BuscarReservaForm(request.POST)
        if form.is_valid():
            busqueda = form.cleaned_data['busqueda'].strip()
            reservas = Reserva.objects.filter(
                Q(codigo__iexact=busqueda) | Q(cliente__email__iexact=busqueda)
            ).select_related('cliente', 'servicio').order_by('-fecha', '-hora')

            if not reservas.exists():
                messages.warning(request, "No se encontraron reservas con ese código o email.")

    return render(request, 'public/mi_reserva.html', {'form': form, 'reservas': reservas})


def cancelar_reserva_publica(request, codigo):
    reserva = get_object_or_404(Reserva, codigo=codigo)
    if request.method == 'POST' and reserva.puede_cancelar:
        reserva.estado = 'cancelada'
        reserva.save()
        messages.success(request, f"Reserva #{reserva.codigo} cancelada correctamente.")
    return redirect('mi_reserva')


def horas_disponibles_api(request):
    """API para obtener horas disponibles por fecha (AJAX)."""
    fecha_str = request.GET.get('fecha')
    if not fecha_str:
        return JsonResponse({'horas': []})
    try:
        fecha = datetime.date.fromisoformat(fecha_str)
    except ValueError:
        return JsonResponse({'horas': []})

    horas = get_horas_disponibles(fecha)
    return JsonResponse({'horas': [
        {'value': h['hora_str'], 'label': f"{h['hora_str']} ({h['disponibles']} disponible{'s' if h['disponibles'] != 1 else ''})"}
        for h in horas
    ]})


# ─── VISTAS PRIVADAS (ADMIN) ───────────────────────────────────────────────────

@login_required
def dashboard(request):
    hoy = timezone.localdate()
    reservas_hoy = Reserva.objects.filter(fecha=hoy)
    proximas = Reserva.objects.filter(
        fecha__gte=hoy,
        estado__in=['pendiente', 'confirmada']
    ).select_related('cliente', 'servicio').order_by('fecha', 'hora')[:10]

    ctx = {
        'total_hoy': reservas_hoy.count(),
        'pendientes_hoy': reservas_hoy.filter(estado='pendiente').count(),
        'confirmadas_hoy': reservas_hoy.filter(estado='confirmada').count(),
        'canceladas_hoy': reservas_hoy.filter(estado='cancelada').count(),
        'proximas': proximas,
        'hoy': hoy,
    }
    return render(request, 'admin_panel/dashboard.html', ctx)


@login_required
def admin_reservas(request):
    form = FiltroReservasForm(request.GET or None)
    reservas = Reserva.objects.select_related('cliente', 'servicio').order_by('-fecha', '-hora')

    if form.is_valid():
        if form.cleaned_data.get('fecha_desde'):
            reservas = reservas.filter(fecha__gte=form.cleaned_data['fecha_desde'])
        if form.cleaned_data.get('fecha_hasta'):
            reservas = reservas.filter(fecha__lte=form.cleaned_data['fecha_hasta'])
        if form.cleaned_data.get('estado'):
            reservas = reservas.filter(estado=form.cleaned_data['estado'])
        if form.cleaned_data.get('servicio'):
            reservas = reservas.filter(servicio=form.cleaned_data['servicio'])

    return render(request, 'admin_panel/reservas.html', {'reservas': reservas, 'form': form})


@login_required
def admin_reserva_detalle(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    return render(request, 'admin_panel/reserva_detalle.html', {'reserva': reserva})


@login_required
@require_POST
def admin_reserva_accion(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    accion = request.POST.get('accion')
    if accion == 'confirmar' and reserva.estado == 'pendiente':
        reserva.estado = 'confirmada'
        reserva.save()
        messages.success(request, f"Reserva #{reserva.codigo} confirmada.")
    elif accion == 'cancelar' and reserva.estado in ('pendiente', 'confirmada'):
        reserva.estado = 'cancelada'
        reserva.save()
        messages.warning(request, f"Reserva #{reserva.codigo} cancelada.")
    elif accion == 'completar' and reserva.estado == 'confirmada':
        reserva.estado = 'completada'
        reserva.save()
        messages.success(request, f"Reserva #{reserva.codigo} marcada como completada.")
    return redirect('admin_reservas')


# ─── SERVICIOS ────────────────────────────────────────────────────────────────

@login_required
def admin_servicios(request):
    servicios = Servicio.objects.all()
    return render(request, 'admin_panel/servicios.html', {'servicios': servicios})


@login_required
def admin_servicio_crear(request):
    form = ServicioForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Servicio creado correctamente.")
        return redirect('admin_servicios')
    return render(request, 'admin_panel/servicio_form.html', {'form': form, 'titulo': 'Nuevo Servicio'})


@login_required
def admin_servicio_editar(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    form = ServicioForm(request.POST or None, instance=servicio)
    if form.is_valid():
        form.save()
        messages.success(request, "Servicio actualizado.")
        return redirect('admin_servicios')
    return render(request, 'admin_panel/servicio_form.html', {'form': form, 'titulo': 'Editar Servicio', 'servicio': servicio})


@login_required
@require_POST
def admin_servicio_eliminar(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    servicio.delete()
    messages.warning(request, f"Servicio '{servicio.nombre}' eliminado.")
    return redirect('admin_servicios')


# ─── HORARIOS ─────────────────────────────────────────────────────────────────

@login_required
def admin_horarios(request):
    horarios = Horario.objects.all()
    fechas_bloqueadas = FechaBloqueada.objects.order_by('fecha')
    form_horario = HorarioForm()
    form_bloqueo = FechaBloqueadaForm()
    return render(request, 'admin_panel/horarios.html', {
        'horarios': horarios,
        'fechas_bloqueadas': fechas_bloqueadas,
        'form_horario': form_horario,
        'form_bloqueo': form_bloqueo,
    })


@login_required
def admin_horario_crear(request):
    if request.method == 'POST':
        form = HorarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Horario creado.")
    return redirect('admin_horarios')


@login_required
@require_POST
def admin_horario_eliminar(request, pk):
    horario = get_object_or_404(Horario, pk=pk)
    horario.delete()
    messages.warning(request, "Horario eliminado.")
    return redirect('admin_horarios')


@login_required
def admin_fecha_bloquear(request):
    if request.method == 'POST':
        form = FechaBloqueadaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fecha bloqueada correctamente.")
    return redirect('admin_horarios')


@login_required
@require_POST
def admin_fecha_desbloquear(request, pk):
    fecha = get_object_or_404(FechaBloqueada, pk=pk)
    fecha.delete()
    messages.success(request, "Fecha desbloqueada.")
    return redirect('admin_horarios')


# ─── CLIENTES ─────────────────────────────────────────────────────────────────

@login_required
def admin_clientes(request):
    clientes = Cliente.objects.annotate(num_reservas=Count('reserva')).order_by('-num_reservas')
    return render(request, 'admin_panel/clientes.html', {'clientes': clientes})


@login_required
def admin_cliente_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    reservas = cliente.reserva_set.select_related('servicio').order_by('-fecha', '-hora')
    return render(request, 'admin_panel/cliente_detalle.html', {'cliente': cliente, 'reservas': reservas})


# ─── REPORTES ─────────────────────────────────────────────────────────────────

@login_required
def admin_reportes(request):
    desde = request.GET.get('desde')
    hasta = request.GET.get('hasta')
    hoy = timezone.localdate()

    if not desde:
        desde = hoy.replace(day=1).isoformat()
    if not hasta:
        hasta = hoy.isoformat()

    reservas = Reserva.objects.filter(
        fecha__gte=desde, fecha__lte=hasta
    )

    servicios_top = reservas.values('servicio__nombre').annotate(
        total=Count('id')
    ).order_by('-total')[:5]

    total = reservas.count()
    canceladas = reservas.filter(estado='cancelada').count()
    tasa_cancelacion = round((canceladas / total * 100) if total > 0 else 0, 1)

    ctx = {
        'desde': desde,
        'hasta': hasta,
        'total': total,
        'pendientes': reservas.filter(estado='pendiente').count(),
        'confirmadas': reservas.filter(estado='confirmada').count(),
        'canceladas': canceladas,
        'completadas': reservas.filter(estado='completada').count(),
        'tasa_cancelacion': tasa_cancelacion,
        'servicios_top': servicios_top,
        'reservas': reservas.select_related('cliente', 'servicio').order_by('fecha', 'hora'),
    }
    return render(request, 'admin_panel/reportes.html', ctx)
