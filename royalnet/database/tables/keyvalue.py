from sqlalchemy import Column, \
                       String, \
                       ForeignKey


class Keyvalue:
    __tablename__ = "keyvalues"

    group = Column(String, ForeignKey("keygroups.group_name"), primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)

    def __repr__(self):
        return f"<Keyvalue group={self.group} key={self.key} value={self.value}>"

    def __str__(self):
        return f"{self.key}: [b]{self.value}[/b]"
