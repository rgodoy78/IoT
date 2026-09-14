from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import UserCreateForm, UserEditForm
from .models import User


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class UserLoginView(LoginView):
    template_name = "users/login.html"


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("users:login")


class UserListView(StaffRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    ordering = ["username"]


class UserCreateView(StaffRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("users:user_list")

    def form_valid(self, form):
        messages.success(self.request, "Usuario creado correctamente.")
        return super().form_valid(form)


class UserUpdateView(StaffRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("users:user_list")

    def form_valid(self, form):
        messages.success(self.request, "Usuario actualizado correctamente.")
        return super().form_valid(form)


class UserDeleteView(StaffRequiredMixin, DeleteView):
    model = User
    template_name = "users/user_confirm_delete.html"
    success_url = reverse_lazy("users:user_list")

    def form_valid(self, form):
        messages.success(self.request, "Usuario eliminado correctamente.")
        return super().form_valid(form)
