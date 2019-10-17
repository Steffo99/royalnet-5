from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       LargeBinary, \
                       DateTime, \
                       ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr


class Reminder:
    __tablename__ = "reminder"

    @declared_attr
    def reminder_id(self):
        return Column(Integer, primary_key=True)

    @declared_attr
    def creator_id(self):
        return Column(Integer, ForeignKey("users.uid"))

    @declared_attr
    def creator(self):
        return relationship("User", backref="reminders_created")

    @declared_attr
    def interface_name(self):
        return Column(String)

    @declared_attr
    def interface_data(self):
        return Column(LargeBinary)

    @declared_attr
    def datetime(self):
        return Column(DateTime)

    @declared_attr
    def message(self):
        return Column(String)

    def __repr__(self):
        return f"<Reminder for {self.datetime.isoformat()} about {self.message}>"

    def __str__(self):
        return self.message
