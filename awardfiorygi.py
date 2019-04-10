import telegram
import configparser
import db
import strings

config = configparser.ConfigParser()
config.read("config.ini")


telegram_bot = telegram.Bot(config["Telegram"]["bot_token"])
session = db.Session()


name = input("Utente Royalnet: ")
user = session.query(db.Royal).filter(db.Royal.username == name).one()
number = int(input("Fiorygi da aggiungere: "))
user.fiorygi += number
reason = input("Motivazione: ")
fiorygi = f"fioryg{'i' if number != 1 else ''}"
telegram_bot.send_message(config["Telegram"]["main_group"],
                          strings.safely_format_string(strings.TELEGRAM.FIORYGI_AWARDED,
                                                       words={
                                                           "mention": user.telegram[0].mention(),
                                                           "number": str(number),
                                                           "fiorygi": fiorygi,
                                                           "reason": reason
                                                       }),
                          parse_mode="HTML",
                          disable_web_page_preview=True)
session.commit()
session.close()
