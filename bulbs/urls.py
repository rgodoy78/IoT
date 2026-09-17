from django.urls import path

from . import views

app_name = "bulbs"

urlpatterns = [
    path("", views.BulbListView.as_view(), name="bulb_list"),
    path("nueva/", views.BulbCreateView.as_view(), name="bulb_create"),
    path("importar/", views.BulbImportView.as_view(), name="bulb_import"),
    path("<int:pk>/", views.BulbDetailView.as_view(), name="bulb_detail"),
    path("<int:pk>/editar/", views.BulbUpdateView.as_view(), name="bulb_edit"),
    path("<int:pk>/eliminar/", views.BulbDeleteView.as_view(), name="bulb_delete"),
    path("<int:pk>/control/", views.BulbControlView.as_view(), name="bulb_control"),
    path("<int:pk>/estado/", views.BulbStatusView.as_view(), name="bulb_status"),
    path("<int:bulb_pk>/programaciones/estado/", views.ScheduleStatusView.as_view(), name="schedule_status"),
    path("<int:bulb_pk>/programaciones/nueva/", views.ScheduleCreateView.as_view(), name="schedule_create_for_bulb"),
    path("programaciones/", views.ScheduleListView.as_view(), name="schedule_list"),
    path("programaciones/nueva/", views.ScheduleCreateView.as_view(), name="schedule_create"),
    path("programaciones/<int:pk>/editar/", views.ScheduleUpdateView.as_view(), name="schedule_edit"),
    path("programaciones/<int:pk>/eliminar/", views.ScheduleDeleteView.as_view(), name="schedule_delete"),
]
