# from apscheduler.schedulers.background import BackgroundScheduler
# from user.views import delete_oldData, conversation_update, validity_update, hit_reminder
# from django.utils import timezone
# from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

# executors = {
#     'default': ThreadPoolExecutor(90),   # max threads: 90
#     'processpool': ProcessPoolExecutor(20)  # max processes 20
# }

# def start():
    # scheduler = BackgroundScheduler(timezone=timezone.utc, executors=executors)
    # scheduler.add_job(delete_oldData, 'interval', hours=24, start_date='2022-11-8 00:00:00')
    # scheduler.add_job(conversation_update, 'interval', seconds=10)
    # scheduler.add_job(validity_update, 'interval', hours=24, start_date='2022-12-13 00:00:00')
    # scheduler.add_job(hit_reminder, 'interval', seconds=30)
    # scheduler.start()
