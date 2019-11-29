from royalnet.commands import *


class ExceptionEvent(Event):
    name = "exception"

    def run(self, **kwargs):
        if not self.interface.config["exc_debug"]:
            raise UserError(f"{self.interface.prefix}{self.name} is not enabled.")
        raise Exception(f"{self.name} event was called")
