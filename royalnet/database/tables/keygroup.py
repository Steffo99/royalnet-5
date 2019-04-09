from sqlalchemy import Column, \
                       String, \
                       ForeignKey


class Keygroup:
    __tablename__ = "keygroups"

    group_name = Column(String, ForeignKey("keygroups.group_name"), primary_key=True)

    def __repr__(self):
        return f"<Keygroup {self.group_name}>"
