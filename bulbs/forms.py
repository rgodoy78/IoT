from django import forms

from .models import DAY_CHOICES, Bulb, ColorSchedule


class BulbForm(forms.ModelForm):
    local_key = forms.CharField(
        label="Local Key",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Al editar, dejalo en blanco para mantener la clave actual.",
    )

    class Meta:
        model = Bulb
        fields = ["name", "device_id", "ip_address", "version", "local_key", "is_active"]
        labels = {
            "name": "Nombre",
            "device_id": "Device ID",
            "ip_address": "Dirección IP local",
            "version": "Versión de protocolo",
            "is_active": "Activa",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ip_address"].required = True
        if not self.instance.pk:
            self.fields["local_key"].required = True

    def clean_local_key(self):
        value = self.cleaned_data.get("local_key")
        if not value and self.instance.pk:
            return self.instance.local_key
        return value


class ColorScheduleForm(forms.ModelForm):
    days_of_week = forms.MultipleChoiceField(
        label="Días",
        choices=DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    bulbs = forms.ModelMultipleChoiceField(
        label="Ampolletas",
        queryset=Bulb.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        help_text="Seleccioná una o varias ampolletas para aplicarles esta programación.",
    )

    class Meta:
        model = ColorSchedule
        fields = [
            "name", "bulbs", "days_of_week", "start_time", "end_time",
            "color_a", "color_b", "min_interval_minutes", "max_interval_minutes", "is_active",
        ]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "color_a": forms.TextInput(attrs={"type": "color"}),
            "color_b": forms.TextInput(attrs={"type": "color"}),
        }
        labels = {
            "name": "Nombre (opcional)",
            "start_time": "Desde",
            "end_time": "Hasta",
            "color_a": "Color A",
            "color_b": "Color B",
            "min_interval_minutes": "Intervalo mínimo (minutos)",
            "max_interval_minutes": "Intervalo máximo (minutos)",
            "is_active": "Activo",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["days_of_week"] = [str(d) for d in self.instance.day_list()]
            self.initial["bulbs"] = list(self.instance.bulbs.values_list("pk", flat=True))

    def clean_days_of_week(self):
        days = self.cleaned_data.get("days_of_week") or []
        return ",".join(sorted(days, key=int))

    def clean(self):
        cleaned = super().clean()
        min_minutes = cleaned.get("min_interval_minutes")
        max_minutes = cleaned.get("max_interval_minutes")
        if min_minutes and max_minutes and min_minutes > max_minutes:
            raise forms.ValidationError("El intervalo mínimo no puede ser mayor al máximo.")
        return cleaned
