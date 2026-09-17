import json
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from users.views import StaffRequiredMixin

from . import services
from .forms import BulbForm, BulkColorForm, ColorScheduleForm
from .models import Bulb, ColorSchedule

DEFAULT_DEVICES_JSON_PATH = Path(settings.BASE_DIR) / "devices.json"
VALID_VERSIONS = {choice[0] for choice in Bulb.VERSION_CHOICES}
DEFAULT_VERSION = "3.3"


class BulbListView(LoginRequiredMixin, ListView):
    model = Bulb
    template_name = "bulbs/bulb_list.html"
    context_object_name = "bulbs"
    ordering = ["name"]


def _fetch_bulb_state(bulb):
    if not bulb.ip_address:
        return {
            "status": None,
            "online": False,
            "state": None,
            "error": "Esta ampolleta no tiene una IP local configurada todavía. Editala para completarla.",
        }
    try:
        dps = services.get_status(bulb)
        return {"status": dps, "online": True, "state": services.summarize(dps), "error": None}
    except services.BulbConnectionError as exc:
        return {"status": None, "online": False, "state": None, "error": str(exc)}


class BulbDetailView(LoginRequiredMixin, DetailView):
    model = Bulb
    template_name = "bulbs/bulb_detail.html"
    context_object_name = "bulb"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_fetch_bulb_state(self.object))
        context["schedules"] = self.object.schedules.all()
        return context


class BulbStatusView(LoginRequiredMixin, View):
    def get(self, request, pk):
        bulb = get_object_or_404(Bulb, pk=pk)
        result = _fetch_bulb_state(bulb)
        return JsonResponse(result)


class ScheduleStatusView(LoginRequiredMixin, View):
    def get(self, request, bulb_pk):
        bulb = get_object_or_404(Bulb, pk=bulb_pk)
        data = []
        for schedule in bulb.schedules.all():
            hex_color = None
            if schedule.in_window and schedule.last_color:
                hex_color = schedule.color_a if schedule.last_color == "a" else schedule.color_b
            data.append({
                "id": schedule.pk,
                "active": schedule.in_window,
                "color": schedule.last_color,
                "hex": hex_color,
            })
        return JsonResponse({"schedules": data})


class BulbCreateView(StaffRequiredMixin, CreateView):
    model = Bulb
    form_class = BulbForm
    template_name = "bulbs/bulb_form.html"
    success_url = reverse_lazy("bulbs:bulb_list")

    def form_valid(self, form):
        messages.success(self.request, "Ampolleta agregada correctamente.")
        return super().form_valid(form)


class BulbUpdateView(StaffRequiredMixin, UpdateView):
    model = Bulb
    form_class = BulbForm
    template_name = "bulbs/bulb_form.html"
    success_url = reverse_lazy("bulbs:bulb_list")

    def form_valid(self, form):
        messages.success(self.request, "Ampolleta actualizada correctamente.")
        return super().form_valid(form)


class BulbDeleteView(StaffRequiredMixin, DeleteView):
    model = Bulb
    template_name = "bulbs/bulb_confirm_delete.html"
    success_url = reverse_lazy("bulbs:bulb_list")

    def form_valid(self, form):
        messages.success(self.request, "Ampolleta eliminada correctamente.")
        return super().form_valid(form)


class BulbControlView(LoginRequiredMixin, View):
    def post(self, request, pk):
        bulb = get_object_or_404(Bulb, pk=pk)
        action = request.POST.get("action")
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        message = None
        try:
            if action == "on":
                services.turn_on(bulb)
                message = f"‘{bulb.name}’ encendida."
            elif action == "off":
                services.turn_off(bulb)
                message = f"‘{bulb.name}’ apagada."
            elif action == "brightness":
                pct = max(1, min(100, int(request.POST.get("value", 0))))
                services.set_brightness(bulb, pct)
                message = f"Brillo de ‘{bulb.name}’ ajustado a {pct}%."
            elif action == "colortemp":
                pct = max(0, min(100, int(request.POST.get("value", 0))))
                services.set_colortemp(bulb, pct)
                message = f"Temperatura de color de ‘{bulb.name}’ ajustada."
            elif action == "color":
                hex_color = request.POST.get("value", "#ffffff").lstrip("#")
                r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
                services.set_color(bulb, r, g, b)
                message = f"Color de ‘{bulb.name}’ actualizado."
            else:
                if is_ajax:
                    return JsonResponse({"ok": False, "error": "Acción desconocida."}, status=400)
                return redirect("bulbs:bulb_detail", pk=bulb.pk)
        except services.BulbConnectionError as exc:
            if is_ajax:
                return JsonResponse({"ok": False, "error": str(exc)}, status=502)
            messages.error(request, str(exc))
            return redirect("bulbs:bulb_detail", pk=bulb.pk)
        except Exception as exc:
            error = f"Error al controlar ‘{bulb.name}’: {exc}"
            if is_ajax:
                return JsonResponse({"ok": False, "error": error}, status=500)
            messages.error(request, error)
            return redirect("bulbs:bulb_detail", pk=bulb.pk)

        if is_ajax:
            return JsonResponse({"ok": True, "message": message})
        messages.success(request, message)
        return redirect("bulbs:bulb_detail", pk=bulb.pk)


class BulkColorView(LoginRequiredMixin, View):
    template_name = "bulbs/bulb_bulk_color.html"
    SESSION_FORM_KEY = "bulbs_bulk_color_last"
    SESSION_SWITCH_KEY = "bulbs_quick_switch_last"

    def _context(self, request, form):
        switch_state = request.session.get(self.SESSION_SWITCH_KEY) or {}
        return {
            "form": form,
            "active_bulbs": Bulb.objects.filter(is_active=True),
            "quick_switch_has_state": bool(switch_state),
            "quick_switch_bulb_ids": set(switch_state.get("bulbs", [])),
            "quick_switch_color_a": switch_state.get("color_a", "#ff0000"),
            "quick_switch_color_b": switch_state.get("color_b", "#0000ff"),
            "quick_switch_active": switch_state.get("active", "a"),
        }

    def get(self, request):
        last = request.session.get(self.SESSION_FORM_KEY) or {}
        form = BulkColorForm(initial={"bulbs": last.get("bulbs", []), "color": last.get("color", "#ffffff")})
        return render(request, self.template_name, self._context(request, form))

    def post(self, request):
        form = BulkColorForm(request.POST)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not form.is_valid():
            if is_ajax:
                errors = " ".join(e for field_errors in form.errors.values() for e in field_errors)
                return JsonResponse({"ok": False, "error": errors or "Datos inválidos."}, status=400)
            return render(request, self.template_name, self._context(request, form))

        bulbs = form.cleaned_data["bulbs"]
        bulb_ids = [str(bulb.pk) for bulb in bulbs]
        hex_color = form.cleaned_data["color"].lstrip("#")
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

        applied = []
        failed = []
        for bulb in bulbs:
            try:
                # set_color ya enciende la ampolleta (envía color + switch en un
                # mismo comando), así que no hace falta un turn_on() previo: eso
                # duplicaba la conexión al dispositivo y sumaba latencia.
                services.set_color(bulb, r, g, b)
                applied.append(bulb.name)
            except services.BulbConnectionError as exc:
                failed.append(f"{bulb.name}: {exc}")

        success_msg = f"Color aplicado a: {', '.join(applied)}." if applied else None
        error_msg = f"No se pudo aplicar el color a: {'; '.join(failed)}." if failed else None

        if is_ajax:
            # Viene del switch rápido: recordamos ambos colores, el lado activo
            # y la selección de ampolletas de esa sección.
            request.session[self.SESSION_SWITCH_KEY] = {
                "bulbs": bulb_ids,
                "color_a": request.POST.get("color_a", "#ff0000"),
                "color_b": request.POST.get("color_b", "#0000ff"),
                "active": request.POST.get("active", "a"),
            }
            if applied:
                return JsonResponse({"ok": True, "message": success_msg, "warning": error_msg})
            return JsonResponse({"ok": False, "error": error_msg or "No se seleccionó ninguna ampolleta."}, status=502)

        # Viene del formulario "Aplicar color": recordamos selección y color.
        request.session[self.SESSION_FORM_KEY] = {"bulbs": bulb_ids, "color": form.cleaned_data["color"]}

        if success_msg:
            messages.success(request, success_msg)
        if error_msg:
            messages.error(request, error_msg)

        return redirect("bulbs:bulb_bulk_color")


class BulbImportView(StaffRequiredMixin, View):
    template_name = "bulbs/bulb_import.html"

    def get(self, request):
        return render(request, self.template_name, {
            "default_path_exists": DEFAULT_DEVICES_JSON_PATH.exists(),
            "default_path": DEFAULT_DEVICES_JSON_PATH,
        })

    def post(self, request):
        uploaded = request.FILES.get("devices_file")
        try:
            if uploaded:
                raw = uploaded.read().decode("utf-8")
            elif DEFAULT_DEVICES_JSON_PATH.exists():
                raw = DEFAULT_DEVICES_JSON_PATH.read_text(encoding="utf-8")
            else:
                messages.error(
                    request,
                    "No se encontró devices.json. Subí el archivo o generalo primero con "
                    "'python -m tinytuya wizard'.",
                )
                return redirect("bulbs:bulb_import")
            data = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            messages.error(request, "El archivo no es un JSON válido.")
            return redirect("bulbs:bulb_import")

        if not isinstance(data, list):
            messages.error(
                request,
                "El formato de devices.json no es el esperado (se esperaba una lista de dispositivos).",
            )
            return redirect("bulbs:bulb_import")

        created = 0
        updated = 0
        skipped = []
        no_ip = []

        for entry in data:
            if not isinstance(entry, dict):
                continue

            device_id = entry.get("id") or entry.get("uuid")
            local_key = entry.get("key")
            name = entry.get("name") or entry.get("product_name") or device_id or "Sin nombre"

            if not device_id or not local_key:
                skipped.append(name)
                continue

            ip_address = entry.get("ip") or None
            version = str(entry.get("version") or DEFAULT_VERSION)
            if version not in VALID_VERSIONS:
                version = DEFAULT_VERSION

            existing = Bulb.objects.filter(device_id=device_id).first()
            if existing:
                existing.name = name
                existing.local_key = local_key
                existing.ip_address = ip_address
                existing.version = version
                existing.save()
                updated += 1
            else:
                Bulb.objects.create(
                    name=name,
                    device_id=device_id,
                    local_key=local_key,
                    ip_address=ip_address,
                    version=version,
                )
                created += 1

            if not ip_address:
                no_ip.append(name)

        messages.success(request, f"Importación completa: {created} creada(s), {updated} actualizada(s).")
        if skipped:
            messages.warning(
                request,
                f"Se omitieron {len(skipped)} dispositivo(s) sin Device ID o Local Key: {', '.join(skipped)}.",
            )
        if no_ip:
            messages.warning(
                request,
                f"Sin IP local detectada (completala manualmente editando la ampolleta): {', '.join(no_ip)}.",
            )

        return redirect("bulbs:bulb_list")


class ScheduleListView(LoginRequiredMixin, ListView):
    model = ColorSchedule
    template_name = "bulbs/schedule_list.html"
    context_object_name = "schedules"

    def get_queryset(self):
        return ColorSchedule.objects.prefetch_related("bulbs").all()


class ScheduleCreateView(StaffRequiredMixin, CreateView):
    model = ColorSchedule
    form_class = ColorScheduleForm
    template_name = "bulbs/schedule_form.html"
    success_url = reverse_lazy("bulbs:schedule_list")

    def get_initial(self):
        initial = super().get_initial()
        bulb_pk = self.kwargs.get("bulb_pk") or self.request.GET.get("bulb")
        if bulb_pk:
            initial["bulbs"] = [bulb_pk]
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Programación creada correctamente.")
        return super().form_valid(form)


class ScheduleUpdateView(StaffRequiredMixin, UpdateView):
    model = ColorSchedule
    form_class = ColorScheduleForm
    template_name = "bulbs/schedule_form.html"
    success_url = reverse_lazy("bulbs:schedule_list")

    def form_valid(self, form):
        messages.success(self.request, "Programación actualizada correctamente.")
        return super().form_valid(form)


class ScheduleDeleteView(StaffRequiredMixin, DeleteView):
    model = ColorSchedule
    template_name = "bulbs/schedule_confirm_delete.html"
    success_url = reverse_lazy("bulbs:schedule_list")

    def form_valid(self, form):
        messages.success(self.request, "Programación eliminada correctamente.")
        return super().form_valid(form)
