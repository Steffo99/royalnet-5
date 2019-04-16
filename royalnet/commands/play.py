import typing
from ..utils import Command, Call
from ..network import Message, RequestSuccessful, RequestError


class PlayMessage(Message):
    def __init__(self, url: str):
        self.url: str = url


class PlayCommand(Command):
    command_name = "play"
    command_description = "Riproduce una canzone in chat vocale."
    command_syntax = "(url)"

    @classmethod
    async def common(cls, call: Call):
        url: str = call.args[0]
        response: typing.Union[RequestSuccessful, RequestError] = await call.net_request(PlayMessage(url), "discord")
        if isinstance(response, RequestSuccessful):
            await call.reply(f"✅ Richiesta la riproduzione di [c]{url}[/c].")
            return
        elif isinstance(response, RequestError):
            await call.reply(f"⚠️ Si è verificato un'errore nella richiesta di riproduzione:\n[c]{response.reason}[/c]")
            return
        raise TypeError(f"Received unexpected response in the PlayCommand: {response.__class__.__name__}")
