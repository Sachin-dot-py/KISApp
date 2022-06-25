from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
from datetime import datetime
from secrets import USERNAME, PASSWORD

# USERNAME = os.environ.get("USERNAME")
# PASSWORD = os.environ.get("PASSWORD")


class KISNET:
    def __init__(self):
        options = Options()
        options.add_argument("headless")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.LINK = f"http://{USERNAME}:{PASSWORD}@my.kis.in"

    def get_announcements(self):
        self.driver.get(self.LINK)
        posts = self.driver.find_elements(by=By.CSS_SELECTOR, value="div.content > table")
        announcements = []
        for post in posts:
            sender, title = post.find_elements(by=By.CSS_SELECTOR, value="td")[0].text.strip().replace("From: ",
                                                                                                       "").split("\n")
            links = {p.text: p.get_attribute("href").replace(f"{USERNAME}:{PASSWORD}", "") for p in
                     post.find_elements(by=By.CSS_SELECTOR, value="td a")}
            content = post.find_elements(by=By.CSS_SELECTOR, value="td")[1].text.strip()
            announcements.append({"sender": sender, "title": title, "links": links, "content": content})
        return announcements

    def get_calendar(self, date: datetime = None):
        """ date : Date in DD/MM/YYYY or as Datetime object"""
        if isinstance(date, datetime):
            date = date.strftime("%d/%m/%Y")
        else:
            pass

        today = datetime.today()
        self.driver.get(f"{self.LINK}/Info/Calendar.aspx")
        calendar = {}
        days = self.driver.find_elements(by=By.CLASS_NAME, value="CalendarDiv")
        for day in days:
            day_num = int(day.find_element(by=By.TAG_NAME, value="td").text)
            cur_date = datetime(today.year, today.month, day_num)
            cur_date = cur_date.strftime("%d/%m/%Y")
            try:
                cycle_day_elem = day.find_element(by=By.CLASS_NAME, value="highlight").text
                cycle_day = int(''.join([n for n in cycle_day_elem if n.isdigit()]))
                special_day = day.find_element(by=By.CLASS_NAME, value="highlight2").text
                calendar[cur_date] = {"Cycle Day": cycle_day, "Special Day": special_day}
            except:
                calendar[cur_date] = {"Cycle Day": 0, "Special Day": None}
        if not date:
            return calendar
        else:
            return calendar[date]

    def get_grade_list(self, grades=[9, 10, 11, 12]):
        students = []
        for grade in grades:
            self.driver.get(f"{self.LINK}/Grades/GradeList.asp?Grade={grade}")
            rows = self.driver.find_elements(by=By.TAG_NAME, value='tr')[2:]
            for row in rows:
                cells = row.find_elements(by=By.TAG_NAME, value='td')
                info = [cell.text for cell in cells]
                studentID = int(row.find_element(by=By.TAG_NAME, value="a").get_attribute('href').split("=")[-1].strip())
                students.append(
                    {"name": info[1].strip(), "grade": grade, "DOB": info[3].strip(), "gender": info[4].strip(),
                     "dorm": info[5].strip(), "house": info[6].strip(), "studentID": studentID})
        return students

    def get_schedule(self, studentID):
        self.driver.get(f"{self.LINK}/Students/StudentSchedule.asp?StudentID={studentID}")
        table = self.driver.find_element(by=By.TAG_NAME, value='table')
        rows = table.find_elements(by=By.TAG_NAME, value='tr')[3:]
        rows.pop(2)  # Remove row for "Tea"
        rows.pop(4)  # Remove row for "Lunch"
        timetable = [[] for _ in range(6)]  # Initialize empty timetable
        for row in rows:
            cells = row.find_elements(by=By.TAG_NAME, value='td')[1:]  # First one shows the period number
            day = 1
            for cell in cells:
                text = cell.text.strip()
                try:
                    name, teacher, location = text.splitlines()
                except:
                    if "Self-Study" in text:
                        name = "Self-Study Period"
                        teacher, location = "", ""
                    elif "Assembly / Classbonding" in text:
                        name = "Assembly / Classbonding"
                        teacher, location = "", ""
                    elif "Study Period" in text:
                        name = "Study Period"
                        teacher = ""
                        location = text.splitlines()[1]
                    else:
                        name, teacher, location = "", "", ""

                period = {'subject': name, 'teacher': teacher, 'location': location}
                timetable[day-1].append(period)
                day += 1
        return timetable
