class MMInterfaceData:
    def __init__(self):
        pass


class MMInterfaceDataTelegram(MMInterfaceData):
    def __init__(self, chat_id: int, message_id: int):
        super().__init__()
        self.chat_id = chat_id
        self.message_id = message_id
