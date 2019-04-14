import typing
from ..utils import Command, Call
from ..network import Message, ErrorMessage


class SummonMessage(Message):
    def __init__(self, channel_name: str):
        self.channel_name: str = channel_name


class SummonSuccessful(Message):
    pass


class SummonError(ErrorMessage):
    pass


class SummonCommand(Command):

    command_name = "summon"
    command_description = "Evoca il bot in un canale vocale."
    command_syntax = "[channelname]"

    @classmethod
    async def common(cls, call: Call):
        channel_name: str = call.args[0].lstrip("#")
        response: typing.Union[SummonSuccessful, SummonError] = await call.net_request(SummonMessage(channel_name), "discord")
        if isinstance(response, SummonError):
            await call.reply(f"⚠️ Si è verificato un'errore nella richiesta di connessione:\n[c]{response.reason}[/c]")
            return
        elif isinstance(response, SummonSuccessful):
            await call.reply(f"✅ Mi sono connesso in [c]#{channel_name}[/c].")
            return
        raise Exception(f"wtf is this: {response}")
