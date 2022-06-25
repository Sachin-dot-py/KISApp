import pymongo
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
import os
from kisnet import KISNET
from databases import AnnouncementsDB, StudentDB, SchedulesDB, CalendarDB

MONGO_LINK = os.environ.get("MONGO_LINK")
client = pymongo.mongo_client.MongoClient(MONGO_LINK)  # For persistent storage of jobs
jobstores = {'mongo': MongoDBJobStore(database="KISApp", collection="jobs", client=client)}
scheduler = BlockingScheduler(jobstores=jobstores)


@scheduler.scheduled_job('interval', id='update_announcements', minutes=30, jitter=900)
def update_announcements():
    announcements = KISNET().get_announcements()
    andb = AnnouncementsDB(MONGO_LINK)
    andb.delete_announcements()
    andb.insert_announcements(announcements)
    print("Updated announcements.")


@scheduler.scheduled_job('interval', id='update_students', days=1, jitter=43200)
def update_students():
    students = KISNET().get_grade_list([9, 10, 11, 12])
    sdb = StudentDB(MONGO_LINK)
    sdb.update_students(students)
    print("Updated students list.")


@scheduler.scheduled_job('interval', id='update_schedules', weeks=1, jitter=172800)
def update_schedules():
    sdb = StudentDB(MONGO_LINK)
    students = sdb.get_students()
    obj = KISNET()
    schedules = []
    for student in students:
        schedule = obj.get_schedule(student['studentID'])
        # Turn schedule into the required dictionary format
        schedule = {f"Day {n+1}": schedule[n] for n in range(6)}
        schedules.append({"studentID": student['studentID'], "schedule": schedule})
    schdb = SchedulesDB(MONGO_LINK)
    schdb.update_schedules(schedules)
    print("Updated schedules.")


@scheduler.scheduled_job('interval', id='update_calendar', days=1, jitter=43200)
def update_calendar():
    calendar = KISNET().get_calendar()
    caldb = CalendarDB(MONGO_LINK)
    caldb.update_calendar(calendar)
    print("Updated calendar.")


if __name__ == '__main__':
    update_schedules()
    scheduler.start()
