.. currentmodule:: royalnet.commands

Royalnet Commands
====================================

A Royalnet Command is a small script that is run whenever a specific message is sent to a Royalnet interface.

A Command code looks like this: ::

    from royalnet.commands import Command

    class PingCommand(Command):
        name = "ping"

        description = "Play ping-pong with the bot."

        def __init__(self, interface):
            # This code is run just once, while the bot is starting
            super().__init__()

        async def run(self, args, data):
            # This code is run every time the command is called
            await data.reply("Pong!")


Creating a new Command
------------------------------------

First, think of a ``name`` for your command.
It's the name your command will be called with: for example, the "spaghetti" command will be called by typing **/spaghetti** in chat.
Try to keep the name as short as possible, while staying specific enough so no other command will have the same name.

Next, create a new Python file with the ``name`` you have thought of.
The previously mentioned "spaghetti" command should have a file called ``spaghetti.py``.

Then, in the first row of the file, import the :py:class:`Command` class from :py:mod:`royalnet`, and create a new class inheriting from it: ::

    from royalnet.commands import Command

    class SpaghettiCommand(Command):
        ...

Inside the class, override the attributes ``name`` and ``description`` with respectively the **name of the command** and a **small description of what the command will do**: ::

    from royalnet.commands import Command

    class SpaghettiCommand(Command):
        name = "spaghetti"

        description = "Send a spaghetti emoji in the chat."

Now override the :py:meth:`Command.run` method, adding the code you want the bot to run when the command is called.

To send a message in the chat the command was called in, you can use the :py:meth:`CommandData.reply` method: ::

    from royalnet.commands import Command

    class SpaghettiCommand(Command):
        name = "spaghetti"

        description = "Send a spaghetti emoji in the chat."

        async def run(self, args, data):
            data.reply("🍝")

And it's done! The command is now ready to be used in a bot!
