from apscheduler.schedulers.blocking import BlockingScheduler
import runpy

sched = BlockingScheduler()

@sched.scheduled_job('cron', hour=0)
def scheduled_job():
    runpy.run_path('shopify_ca_updater.py')
    runpy.run_path('shopify_us_updater.py')

sched.start()
