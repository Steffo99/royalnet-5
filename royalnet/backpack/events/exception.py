from royalnet.commands import *


class ExceptionEvent(Event):
    name = "exception"

    def run(self, **kwargs):
        raise Exception(f"{self.name} event was called")
