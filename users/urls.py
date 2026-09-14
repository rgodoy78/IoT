from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("", views.UserListView.as_view(), name="user_list"),
    path("nuevo/", views.UserCreateView.as_view(), name="user_create"),
    path("<int:pk>/editar/", views.UserUpdateView.as_view(), name="user_edit"),
    path("<int:pk>/eliminar/", views.UserDeleteView.as_view(), name="user_delete"),
]
