from apscheduler.schedulers.background import BackgroundScheduler
from user.views import delete_oldData, conversation_update
from django.utils import timezone


def start():
    scheduler = BackgroundScheduler(timezone=timezone.utc)
    scheduler.add_job(delete_oldData, 'interval', hours=24, start_date='2022-11-8 00:00:00')
    scheduler.add_job(conversation_update, 'interval', seconds=10)
    scheduler.start()
