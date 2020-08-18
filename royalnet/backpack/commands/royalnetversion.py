import pkg_resources

from royalnet.commands import *


class RoyalnetversionCommand(Command):
    name: str = "royalnetversion"

    description: str = "Display the current Royalnet version."

    @property
    def royalnet_version(self):
        return pkg_resources.get_distribution("royalnet").version

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        # noinspection PyUnreachableCode
        if __debug__:
            message = f"ℹ️ Royalnet [url=https://github.com/Steffo99/royalnet/]Unreleased[/url]\n"
        else:
            message = f"ℹ️ Royalnet [url=https://github.com/Steffo99/royalnet/releases/tag/{self.royalnet_version}]" \
                      f"{self.royalnet_version}[/url]\n"
        if "69" in self.royalnet_version:
            message += "(Nice.)"
        await data.reply(message)
