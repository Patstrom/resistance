from apscheduler.schedulers.blocking import BlockingScheduler
from advancer import *

sched = BlockingScheduler()

@sched.scheduled_job('cron', hour=0)
def scheduled_job():
    advancer.advance_games()

sched.start()
