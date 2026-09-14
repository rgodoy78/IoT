import os

from django.apps import AppConfig


class BulbsConfig(AppConfig):
    name = 'bulbs'

    def ready(self):
        if os.environ.get("RUN_MAIN") != "true":
            return

        from apscheduler.schedulers.background import BackgroundScheduler

        from . import scheduler as bulb_scheduler

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            bulb_scheduler.run_tick,
            "interval",
            minutes=1,
            id="bulb_schedule_tick",
            replace_existing=True,
        )
        scheduler.start()
