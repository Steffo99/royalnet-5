from royalnet.commands import *


class ExceptionEvent(HeraldEvent):
    name = "exception"

    def run(self, **kwargs):
        if not self.config["exc_debug"]:
            raise UserError(f"{self.__class__.__name__} is not enabled.")
        raise Exception(f"{self.name} event was called")
