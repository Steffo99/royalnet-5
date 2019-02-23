import telegram
import configparser
config = configparser.ConfigParser()
config.read("config.ini")


telegram_bot = telegram.Bot(config["Telegram"]["bot_token"])


while True:
    message = input()
    telegram_bot.send_message(config["Telegram"]["main_group"], message,
                              parse_mode="HTML",
                              disable_web_page_preview=True)
