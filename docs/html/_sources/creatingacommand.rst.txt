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

Then, in the first row of the file, import the :py:class:`Command` class from royalnet, and create a new class inheriting from it: ::

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
            await data.reply("🍝")

And... it's done! The command is ready to be added to a bot!

Coroutines and slow operations
------------------------------------

You may have noticed that in the previous example I wrote ``await data.reply("🍝")`` instead of just ``data.reply("🍝")``.

This is because :py:meth:`CommandData.reply` isn't a simple method: it is a coroutine, a special kind of function that
 can be executed separately from the rest of the code, allowing the bot to do other things in the meantime.

By adding the ``await`` keyword before the ``data.reply("🍝")``, we tell the bot that it can do other things, like
 receiving new messages, while the message is being sent.

You should avoid running slow normal functions inside bot commands, as they will stop the bot from working until they
 are finished and may cause bugs in other parts of the code! ::

    async def run(self, args, data):
        # Don't do this!
        image = download_1_terabyte_of_spaghetti("right_now", from="italy")
        ...

If the slow function you want does not cause any side effect, you can wrap it with the :ref:`royalnet.utils.asyncify`
 function: ::

    async def run(self, args, data):
        # If the called function has no side effect, you can do this!
        image = await asyncify(download_1_terabyte_of_spaghetti, "right_now", from="italy")
        ...

Avoid using :py:func:`time.sleep` function, as it is considered a slow operation: use instead :py:func:`asyncio.sleep`,
 a coroutine that does the same exact thing.
