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

Command arguments
------------------------------------

A command can have some arguments passed by the user: for example, on Telegram an user may type `/spaghetti carbonara al-dente`
to pass the :py:class:`str` `"carbonara al-dente"` to the command code.

These arguments can be accessed in multiple ways through the ``args`` parameter passed to the :py:meth:`Command.run`
method.

If you want your command to use arguments, override the ``syntax`` class attribute with a brief description of the
syntax of your command, possibly using (round parentheses) for required arguments and [square brackets] for optional
ones. ::

    from royalnet.commands import Command

    class SpaghettiCommand(Command):
        name = "spaghetti"

        description = "Send a spaghetti emoji in the chat."

        syntax = "(requestedpasta)"

        async def run(self, args, data):
            await data.reply(f"🍝 Here's your {args[0]}!")


Direct access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can consider arguments as if they were separated by spaces.

You can then access command arguments directly by number as if the args object was a list of :py:class:`str`.

If you request an argument with a certain number, but the argument does not exist, an
:py:exc:`royalnet.error.InvalidInputError` is raised, making the arguments accessed in this way **required**. ::

    args[0]
    # "carbonara"

    args[1]
    # "al-dente"

    args[2]
    # InvalidInputError() is raised

Optional access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't want arguments to be required, you can access them through the :py:meth:`CommandArgs.optional` method: it
will return :py:const:`None` if the argument wasn't passed, making it **optional**. ::

    args.optional(0)
    # "carbonara"

    args.optional(1)
    # "al-dente"

    args.optional(2)
    # None

You can specify a default result too, so that the method will return it instead of returning :py:const:`None`: ::

    args.optional(2, default="banana")
    # "banana"

Full string
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want the full argument string, you can use the :py:meth:`CommandArgs.joined` method. ::

    args.joined()
    # "carbonara al-dente"

You can specify a minimum number of arguments too, so that an :py:exc:`royalnet.error.InvalidInputError` will be
raised if not enough arguments are present: ::

    args.joined(require_at_least=3)
    # InvalidInputError() is raised

Regular expressions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For more complex commands, you may want to get arguments through `regular expressions <https://regexr.com/>`_.

You can then use the :py:meth:`CommandArgs.match` method, which tries to match a pattern to the command argument string,
which returns a tuple of the matched groups and raises an :py:exc:`royalnet.error.InvalidInputError` if there is no match.

To match a pattern, :py:func:`re.match` is used, meaning that Python will try to match only at the beginning of the string. ::

    args.match(r"(carb\w+)")
    # ("carbonara",)

    args.match(r"(al-\w+)")
    # InvalidInputError() is raised

    args.match(r"\s*(al-\w+)")
    # ("al-dente",)

    args.match(r"\s*(carb\w+)\s*(al-\w+)")
    # ("carbonara", "al-dente")

Running code at the initialization of the bot
------------------------------------

You can run code while the bot is starting by overriding the :py:meth:`Command.__init__` function.

You should keep the ``super().__init__(interface)`` call at the start of it, so that the :py:class:`Command` instance is
initialized properly, then add your code after it.

You can add fields to the command to keep **shared data between multiple command calls** (but not bot restarts): it may
be useful for fetching external static data and keeping it until the bot is restarted, or to store references to all the
:py:class:`asyncio.Task` started by the bot. ::

    from royalnet.commands import Command

    class SpaghettiCommand(Command):
        name = "spaghetti"

        description = "Send a spaghetti emoji in the chat."

        syntax = "(pasta)"

        def __init__(self, interface):
            super().__init__(interface)
            self.requested_pasta = []

        async def run(self, args, data):
            pasta = args[0]
            if pasta in self.requested_pasta:
                await data.reply(f"⚠️ This pasta was already requested before.")
                return
            self.requested_pasta.append(pasta)
            await data.reply(f"🍝 Here's your {pasta}!")


Coroutines and slow operations
------------------------------------

You may have noticed that in the previous examples we used ``await data.reply("🍝")`` instead of just ``data.reply("🍝")``.

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

If the slow function you want does not cause any side effect, you can wrap it with the :py:func:`royalnet.utils.asyncify`
function: ::

    async def run(self, args, data):
        # If the called function has no side effect, you can do this!
        image = await asyncify(download_1_terabyte_of_spaghetti, "right_now", from="italy")
        ...

Avoid using :py:func:`time.sleep` function, as it is considered a slow operation: use instead :py:func:`asyncio.sleep`,
a coroutine that does the same exact thing.

Accessing the database
------------------------------------

.. Usually, bots are connected to a PostgreSQL database through a :py:class:`royalnet.database.Alchemy` interface (which is
itself a SQLAlchemy wrapper).

.. Commands can access the connected database through the :py:class:`royalnet.database.Alchemy` available at
``self.interface.alchemy``, and can access the database session at ``self.interface.session``.

Comunicating via Royalnet
------------------------------------
