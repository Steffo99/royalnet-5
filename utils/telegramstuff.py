import telegram
import strings


def reply_msg(bot: telegram.Bot, chat_id: int, string: str, ignore_escaping=False, disable_web_page_preview=True, **kwargs) -> telegram.Message:
    string = strings.safely_format_string(string, ignore_escaping=ignore_escaping, words=kwargs)
    return bot.send_message(chat_id, string,
                            parse_mode="HTML",
                            disable_web_page_preview=disable_web_page_preview)
