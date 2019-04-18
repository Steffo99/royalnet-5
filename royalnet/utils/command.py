import typing
if typing.TYPE_CHECKING:
    from .call import Call


class Command:
    """A generic command, called from any source."""

    command_name: str = NotImplemented
    command_description: str = NotImplemented
    command_syntax: str = NotImplemented

    require_alchemy_tables: typing.Set = set()

    async def common(self, call: "Call"):
        raise NotImplementedError()
