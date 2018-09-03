from apscheduler.schedulers.blocking import BlockingScheduler
import aw
import skymet
import jaihanuman
import sms_add
import power

sched = BlockingScheduler()

# @sched.scheduled_job('interval', minutes=3)
# def timed_job():
#     print('This job is run every three minutes.')

# @sched.scheduled_job('cron', day_of_week='mon-sun', hour=18)
# def scheduled_job1():

#   aw.fetch_aw('aw')
#   # skymet.fetch_sm()

# @sched.scheduled_job('cron', day_of_week='mon-sun', hour=6)
# def scheduled_job2():

#   aw.fetch_aw('aw')
#   # skymet.fetch_sm()

@sched.scheduled_job('interval', minutes=10)
def scheduled_job1():
	sms_add.SMSadd()
	power.power_scraper()

# @sched.scheduled_job('interval', days=1)
# def scheduled_job3():
#     aw.fetch_aw()
#     skymet.fetch_sm()

# @sched.scheduled_job('interval', days = 1)
# def scheduled_job2():
#     jaihanuman.goodHindu()

sched.start()