from flask import Flask
from flask_apscheduler import APScheduler
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pymongo
import json
import os

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)

USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
MONGO_LINK = os.environ.get("MONGO_LINK")

class KISNET:
    def __init__(self):
        options = Options()
        # options.add_argument("headless")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.LINK = f"http://{USERNAME}:{PASSWORD}@my.kis.in"

    def get_announcements(self):
        self.driver.get(self.LINK)
        posts = self.driver.find_elements(by=By.CSS_SELECTOR, value="div.content > table")
        announcements = []
        for post in posts:
            sender, title = post.find_elements(by=By.CSS_SELECTOR, value="td")[0].text.strip().replace("From: ","").split("\n")
            links = {p.text : p.get_attribute("href").replace(f"{USERNAME}:{PASSWORD}","") for p in post.find_elements(by=By.CSS_SELECTOR, value="td a")}
            content = post.find_elements(by=By.CSS_SELECTOR, value="td")[1].text.strip()
            announcements.append({"sender" : sender, "title" : title, "links" : links, "content" : content})
        return announcements

    def get_cycle_day(self, date=None):
        self.driver.get(f"{self.LINK}/Info/Calendar.aspx")
        cycle_days = {}
        days = self.driver.find_elements(by=By.CLASS_NAME, value="CalendarDiv")
        for day in days:
            try:
                day_num = int(day.find_element(by=By.TAG_NAME, value="td").text)
                cycle_day = day.find_elements(by=By.CLASS_NAME, value="highlight")[0].text
                cycle_days[day_num] = int(''.join([n for n in cycle_day if n.isdigit()]))
            except:
                cycle_days[day_num] = None
        if not date:
            return cycle_days
        else:
            return cycle_days[date]

    def get_calendar(self, date=None):
        self.driver.get(f"{self.LINK}/Info/Calendar.aspx")
        special_days = {}
        days = self.driver.find_elements(by=By.CLASS_NAME, value="CalendarDiv")
        for day in days:
            try:
                day_num = int(day.find_element(by=By.TAG_NAME, value="td").text)
                special_day = day.find_element(by=By.CLASS_NAME, value="highlight2").text
                special_days[day_num] = special_day
            except:
                special_days[day_num] = None
        if not date:
            return special_days
        else:
            return special_days[date]

    def getGradeList(self, grades=[9,10,11,12]):
        students = []
        for grade in grades:
            self.driver.get(f"{self.LINK}/Grades/GradeList.asp?Grade={grade}")
            rows = self.driver.find_elements_by_tag_name('tr')[2:]
            for row in rows:
                cells = row.find_elements_by_tag_name('td')
                info = [cell.text for cell in cells]
                studentID = int(row.find_element_by_tag_name("a").get_attribute('href').split("=")[-1].strip())
                students.append({"name" : info[1].strip(), "grade" : grade, "DOB" : info[3].strip(), "gender" : info[4].strip(), "dorm" : info[5].strip(), "house" : info[6].strip(), "studentID" : studentID})
        return students

    def getSchedule(self, studentID):
        self.driver.get(f"{self.LINK}/Students/StudentSchedule.asp?StudentID={studentID}")
        table = self.driver.find_element_by_tag_name('table')
        rows = table.find_elements_by_tag_name('tr')[3:]
        timetable = []
        for row in rows:
            cells = row.find_elements_by_tag_name('td')
            classes = [cell.text.strip() for cell in cells]
            timetable.append(classes)
        return timetable

class AnnouncementsDB:
    def __init__(self, link: str):
        self.client = pymongo.MongoClient(link, server_api=pymongo.server_api.ServerApi('1'))
        self.db = self.client.KISApp
        self.col = self.db.announcements

    def insert_announcements(self, announcements: list[dict]):
        result = self.col.insert_many(announcements)
        return result

    def delete_announcements(self):
        result = self.col.delete_many({})
        return result

    def get_announcements(self):
        announcements = self.col.find({}, {"_id": 0})
        return list(announcements)

# @scheduler.task('cron', id='get_note', hour=12) # every day at noon
# def get_notes():
#     return 'blablabla'


@scheduler.task('interval', id='update_announcements', minutes=30, misfire_grace_time=900)
def update_announcements():
    announcements = KISNET().get_announcements()
    andb = AnnouncementsDB(MONGO_LINK)
    andb.delete_announcements()
    andb.insert_announcements(announcements)

# @scheduler.task('interval', id='update_announcements', minutes=30, misfire_grace_time=900)
# def announcements():
#     announcements = KISNET().get_announcements()
#     andb = AnnouncementsDB()
#     andb.delete_announcements()
#     andb.insert_announcements(announcements)

# cron examples
# @scheduler.task('cron', id='update_cycle_days', day='*')
# def cycle_days():
#     print('Job 2 executed')


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/announcements")
def announcements():
    return json.dumps(AnnouncementsDB(MONGO_LINK).get_announcements())

if __name__ == "__main__":
    scheduler.start()
    app.run()
