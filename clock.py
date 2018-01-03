from apscheduler.schedulers.blocking import BlockingScheduler
from bin import advancer

sched = BlockingScheduler()

@sched.scheduled_job('cron', hour=0)
def scheduled_job():
    advancer.advance_games()

sched.start()
