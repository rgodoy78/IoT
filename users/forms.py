from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User

FIELD_LABELS = {
    "username": "Usuario",
    "email": "Correo electrónico",
    "first_name": "Nombre",
    "last_name": "Apellido",
    "is_staff": "Administrador",
    "is_active": "Activo",
}


class UserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
        labels = FIELD_LABELS


class UserEditForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
        labels = FIELD_LABELS
