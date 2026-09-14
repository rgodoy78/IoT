from django import forms
from django.contrib import admin

from .models import Bulb


class BulbAdminForm(forms.ModelForm):
    local_key = forms.CharField(widget=forms.PasswordInput(render_value=True), label="Local Key")

    class Meta:
        model = Bulb
        fields = "__all__"


@admin.register(Bulb)
class BulbAdmin(admin.ModelAdmin):
    form = BulbAdminForm
    list_display = ("name", "ip_address", "version", "is_active", "updated_at")
    list_filter = ("is_active", "version")
    search_fields = ("name", "device_id", "ip_address")
