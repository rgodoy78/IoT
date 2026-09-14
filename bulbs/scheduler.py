import logging
import random
from datetime import timedelta

from django.db import close_old_connections
from django.utils import timezone

from . import services
from .models import ColorSchedule

logger = logging.getLogger(__name__)


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _next_interval(schedule, now):
    minutes = random.randint(schedule.min_interval_minutes, schedule.max_interval_minutes)
    return now + timedelta(minutes=minutes)


def _is_in_window(schedule, now):
    days = schedule.day_list()
    current_time = now.time()
    if schedule.start_time <= schedule.end_time:
        return now.weekday() in days and schedule.start_time <= current_time <= schedule.end_time
    if current_time >= schedule.start_time:
        return now.weekday() in days
    if current_time <= schedule.end_time:
        yesterday = (now - timedelta(days=1)).weekday()
        return yesterday in days
    return False


def run_tick():
    close_old_connections()
    now = timezone.localtime()
    for schedule in ColorSchedule.objects.filter(is_active=True).select_related("bulb"):
        try:
            active = _is_in_window(schedule, now)
            if active and not schedule.in_window:
                services.turn_on(schedule.bulb)
                services.set_color(schedule.bulb, *_hex_to_rgb(schedule.color_a))
                schedule.last_color = "a"
                schedule.next_run_at = _next_interval(schedule, now)
                schedule.in_window = True
                schedule.save(update_fields=["last_color", "next_run_at", "in_window"])
            elif active and schedule.next_run_at and now >= schedule.next_run_at:
                next_color = "b" if schedule.last_color == "a" else "a"
                hex_color = schedule.color_b if next_color == "b" else schedule.color_a
                services.set_color(schedule.bulb, *_hex_to_rgb(hex_color))
                schedule.last_color = next_color
                schedule.next_run_at = _next_interval(schedule, now)
                schedule.save(update_fields=["last_color", "next_run_at"])
            elif not active and schedule.in_window:
                services.turn_off(schedule.bulb)
                schedule.in_window = False
                schedule.next_run_at = None
                schedule.last_color = None
                schedule.save(update_fields=["in_window", "next_run_at", "last_color"])
        except services.BulbConnectionError as exc:
            logger.warning("Programación %s: %s", schedule.pk, exc)
    close_old_connections()
