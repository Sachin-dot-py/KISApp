import pymongo


class AnnouncementsDB:
    def __init__(self, link: str):
        self.client = pymongo.MongoClient(link, server_api=pymongo.server_api.ServerApi('1'))
        self.db = self.client.KISApp
        self.col = self.db.announcements

    def insert_announcements(self, announcements):
        result = self.col.insert_many(announcements)
        return result

    def delete_announcements(self):
        result = self.col.delete_many({})
        return result

    def get_announcements(self):
        announcements = self.col.find({}, {"_id": 0})
        return list(announcements)


class StudentDB:
    def __init__(self, link: str):
        self.client = pymongo.MongoClient(link, server_api=pymongo.server_api.ServerApi('1'))
        self.db = self.client.KISApp
        self.col = self.db.students

    def update_students(self, students):
        operations = [pymongo.operations.ReplaceOne(
            filter={"studentID": student["studentID"]},
            replacement=student,
            upsert=True
        ) for student in students]

        #  Delete students who have left/graduated
        self.col.delete_many(
            filter={"studentID": {"$nin": [student["studentID"] for student in students]}}
        )

        result = self.col.bulk_write(operations, ordered=False)
        return result

    def get_students(self, grade=None):
        if grade:
            students = self.col.find({'grade': grade}, {"_id": 0})
        else:
            students = self.col.find({}, {"_id": 0})
        return list(students)


class SchedulesDB:
    def __init__(self, link: str):
        self.client = pymongo.MongoClient(link, server_api=pymongo.server_api.ServerApi('1'))
        self.db = self.client.KISApp
        self.col = self.db.schedules

    def update_schedules(self, students):
        """
        Example students dict:
        students = [
                    { "studentID" : 6609,
                    "schedule" : {
                        "Day 1" : {
                            "Period 1" : {
                                    "Subject" : "Math AA HL",
                                    "Teacher" : "Mr. XYZ",
                                    "Location" : "Room No. 15"
                            }
                        ...
        """
        operations = [pymongo.operations.ReplaceOne(
            filter={"studentID": student["studentID"]},
            replacement=student,
            upsert=True
        ) for student in students]

        result = self.col.bulk_write(operations, ordered=False)
        return result

    def get_schedules(self, studentID=None):
        if studentID:
            student = self.col.find_one({'studentID': studentID}, {"_id": 0})
            return dict(student)
        else:
            students = self.col.find({}, {"_id": 0})
            return list(students)


class CalendarDB:
    def __init__(self, link: str):
        self.client = pymongo.MongoClient(link, server_api=pymongo.server_api.ServerApi('1'))
        self.db = self.client.KISApp
        self.col = self.db.calendar

    def update_calendar(self, calendar):
        operations = [pymongo.operations.ReplaceOne(
            filter={"Date": date},
            replacement={"Date": date, **values},
            upsert=True
        ) for date, values in calendar.items()]

        result = self.col.bulk_write(operations, ordered=False)
        return result

    def get_calendar(self, date: str = None):
        """ date : Date in DD/MM/YYYY format"""
        if date:
            cal = self.col.find_one({'date': date}, {"_id": 0})
            return dict(cal)
        else:
            cal = self.col.find({}, {"_id": 0})
            return list(cal)
