import pickle
from sqlalchemy import *
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr


class MMEvent:
    __tablename__ = "mmevents"

    @declared_attr
    def creator_id(self):
        return Column(Integer, ForeignKey("users.uid"), nullable=False)

    @declared_attr
    def creator(self):
        return relationship("User", backref="mmevents_created")

    @declared_attr
    def mmid(self):
        return Column(Integer, primary_key=True)

    @declared_attr
    def datetime(self):
        return Column(DateTime, nullable=False)

    @declared_attr
    def title(self):
        return Column(String, nullable=False)

    @declared_attr
    def description(self):
        return Column(Text, nullable=False, default="")

    @declared_attr
    def interface(self):
        return Column(String, nullable=False)

    @declared_attr
    def raw_interface_data(self):
        # The default is a pickled None
        return Column(Binary, nullable=False, default=b'\x80\x03N.')

    @property
    def interface_data(self):
        return pickle.loads(self.raw_interface_data)

    @interface_data.setter
    def interface_data(self, value):
        self.raw_interface_data = pickle.dumps(value)

    def __repr__(self):
        return f"<MMEvent {self.mmid}: {self.title}>"
