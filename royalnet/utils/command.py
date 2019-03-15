import typing
if typing.TYPE_CHECKING:
    from .call import Call


class Command:
    """A generic command, called from any source."""

    command_name: str = NotImplemented
    command_title: str = NotImplemented

    async def common(self, call: "Call", *args, **kwargs):
        raise NotImplementedError()
