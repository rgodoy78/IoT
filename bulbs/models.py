from django.db import models

DAY_CHOICES = [
    (0, "Lunes"),
    (1, "Martes"),
    (2, "Miércoles"),
    (3, "Jueves"),
    (4, "Viernes"),
    (5, "Sábado"),
    (6, "Domingo"),
]


class Bulb(models.Model):
    VERSION_CHOICES = [
        ("3.1", "3.1"),
        ("3.3", "3.3"),
        ("3.4", "3.4"),
        ("3.5", "3.5"),
    ]

    name = models.CharField("Nombre", max_length=100)
    device_id = models.CharField("Device ID", max_length=64, unique=True)
    local_key = models.CharField("Local Key", max_length=64)
    ip_address = models.GenericIPAddressField("Dirección IP local", blank=True, null=True)
    version = models.CharField(
        "Versión de protocolo", max_length=4, choices=VERSION_CHOICES, default="3.3"
    )
    is_active = models.BooleanField("Activa", default=True)
    created_at = models.DateTimeField("Creada", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizada", auto_now=True)

    class Meta:
        verbose_name = "Ampolleta"
        verbose_name_plural = "Ampolletas"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ColorSchedule(models.Model):
    bulbs = models.ManyToManyField(Bulb, related_name="schedules", verbose_name="Ampolletas")
    name = models.CharField("Nombre", max_length=100, blank=True)
    days_of_week = models.CharField("Días", max_length=20, help_text="0=Lunes ... 6=Domingo, separados por coma")
    start_time = models.TimeField("Desde")
    end_time = models.TimeField("Hasta")
    color_a = models.CharField("Color A", max_length=7, default="#ff0000")
    color_b = models.CharField("Color B", max_length=7, default="#0000ff")
    min_interval_minutes = models.PositiveIntegerField("Intervalo mínimo (min)", default=5)
    max_interval_minutes = models.PositiveIntegerField("Intervalo máximo (min)", default=15)
    is_active = models.BooleanField("Activo", default=True)

    in_window = models.BooleanField(default=False)
    last_color = models.CharField(max_length=1, choices=[("a", "A"), ("b", "B")], null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField("Creada", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizada", auto_now=True)

    class Meta:
        verbose_name = "Programación de color"
        verbose_name_plural = "Programaciones de color"
        ordering = ["start_time"]

    def __str__(self):
        return self.name or f"Programación {self.start_time}-{self.end_time}"

    def day_list(self):
        return [int(x) for x in self.days_of_week.split(",") if x != ""]

    def days_display(self):
        names = dict(DAY_CHOICES)
        return ", ".join(names[d] for d in self.day_list())

    def bulbs_display(self):
        return ", ".join(self.bulbs.values_list("name", flat=True))
