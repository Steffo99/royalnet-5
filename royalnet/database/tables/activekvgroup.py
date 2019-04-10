from sqlalchemy import Column, \
                       String, \
                       Integer, \
                       ForeignKey
from sqlalchemy.orm import relationship


class ActiveKvGroup:
    __tablename__ = "activekvgroups"

    royal_id = Column(Integer, ForeignKey("royals.uid"), primary_key=True)
    group_name = Column(String, ForeignKey("keygroups.group_name"), nullable=False)

    royal = relationship("Royal", backref="active_kv_group")
    group = relationship("Keygroup", backref="users_with_this_active")

    def __repr__(self):
        return f"<ActiveKvGroup royal={self.royal} group={self.group_name}>"
