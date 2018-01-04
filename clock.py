from apscheduler.schedulers.blocking import BlockingScheduler
from advancer import advance_games

sched = BlockingScheduler()

@sched.scheduled_job('cron', hour=0, minute=30)
def scheduled_job():
    advance_games()

sched.start()
