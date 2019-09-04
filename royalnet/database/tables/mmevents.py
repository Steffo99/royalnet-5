import telegram
import typing
from sqlalchemy import Column, \
                       Integer, \
                       DateTime, \
                       String, \
                       Text, \
                       ForeignKey, \
                       BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from .royals import Royal
if typing.TYPE_CHECKING:
    from .mmdecisions import MMDecision
    from .mmresponse import MMResponse


class MMEvent:
    __tablename__ = "mmevents"

    @declared_attr
    def creator_id(self):
        return Column(Integer, ForeignKey("royals.uid"), nullable=False)

    @declared_attr
    def creator(self):
        return relationship("Royal", backref="mmevents_created")

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
    def state(self):
        # Valid states are WAITING, DECISION, READY_CHECK, STARTED
        return Column(String, nullable=False, default="WAITING")

    @declared_attr
    def message_id(self):
        return Column(BigInteger)

    def __repr__(self):
        return f"<MMEvent {self.mmid}: {self.title}>"

    def __str__(self):
        text = f"🌐 [b]{self.title}[/b] - [b]{self.datetime.strftime('%Y-%m-%d %H:%M')}[/b]\n"
        if self.description:
           text += f"{self.description}\n"
        text += "\n"
        if self.state == "WAITING" or self.state == "DECISION":
            for mmdecision in self.decisions:
                mmdecision: "MMDecision"
                if mmdecision.decision == "YES":
                    text += "🔵 "
                elif mmdecision.decision == "MAYBE":
                    text += "⚫️ "
                elif mmdecision.decision == "NO":
                    text += "🔴 "
                else:
                    raise ValueError(f"decision is of an unknown value ({mmdecision.decision})")
                text += f"{mmdecision.royal}\n"
        elif self.state == "READY_CHECK":
            for mmresponse in self.responses:
                mmresponse: "MMResponse"
                if mmresponse.response is None:
                    text += "❔ "
                elif mmresponse.response == "YES":
                    text += "✅ "
                elif mmresponse.response == "LATER":
                    text += "🕒 "
                elif mmresponse.response == "NO":
                    text += "❌ "
                else:
                    raise ValueError(f"response is of an unknown value ({mmresponse.response})")
                text += f"{mmresponse.royal}\n"
        elif self.state == "STARTED":
            for mmresponse in self.responses:
                if mmresponse.response == "YES":
                    text += f"✅ {mmresponse.royal}\n"
        return text

    def main_keyboard(self) -> typing.Optional[telegram.InlineKeyboardMarkup]:
        if self.state == "WAITING":
            return telegram.InlineKeyboardMarkup([
                [telegram.InlineKeyboardButton("🔵 Ci sarò!", callback_data=f"mm_{self.mmid}_d_YES")],
                [telegram.InlineKeyboardButton("⚫️ Forse...", callback_data=f"mm_{self.mmid}_d_MAYBE")],
                [telegram.InlineKeyboardButton("🔴 Non mi interessa.", callback_data=f"mm_{self.mmid}_d_NO")]
            ])
        elif self.state == "DECISION":
            return telegram.InlineKeyboardMarkup([
                [telegram.InlineKeyboardButton("🔵 Ci sarò!", callback_data=f"mm_{self.mmid}_d_YES"),
                 telegram.InlineKeyboardButton("🔴 Non mi interessa...", callback_data=f"mm_{self.mmid}_d_NO")]
            ])
        elif self.state == "READY_CHECK":
            return telegram.InlineKeyboardMarkup([
                [telegram.InlineKeyboardButton("🚩 Avvia la partita", callback_data=f"mm_{self.mmid}_start")]
            ])
        elif self.state == "STARTED":
            return None
        else:
            raise ValueError(f"state is of an unknown value ({self.state})")
