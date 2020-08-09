.. currentmodule:: royalnet.commands

Creating a new Command
====================================

A Royalnet Command is a small script that is run whenever a specific message is sent to a Royalnet platform.

A Command code looks like this: ::

    import royalnet.commands as rc

    class PingCommand(rc.Command):
        name = "ping"

        description = "Play ping-pong with the bot."

        # This code is run just once, while the bot is starting
        def __init__(self, serf: "Serf", config):
            super().__init__(serf=serf, config=config)

        # This code is run every time the command is called
        async def run(self, args: rc.CommandArgs, data: rc.CommandData):
            await data.reply("Pong!")

Creating a new Command
------------------------------------

First, think of a ``name`` for your command.
It's the name your command will be called with: for example, the "spaghetti" command will be called by typing **/spaghetti** in chat.
Try to keep the name as short as possible, while staying specific enough so no other command will have the same name.

Next, create a new Python file with the ``name`` you have thought of.
The previously mentioned "spaghetti" command should have a file called ``spaghetti.py``.

Then, in the first row of the file, import the :class:`~Command` class from royalnet, and create a new class inheriting from it: ::

    import royalnet.commands as rc

    class SpaghettiCommand(rc.Command):
        ...

Inside the class, override the attributes ``name`` and ``description`` with respectively the **name of the command** and a **small description of what the command will do**: ::

    import royalnet.commands as rc

    class SpaghettiCommand(rc.Command):
        name = "spaghetti"

        description = "Send a spaghetti emoji in the chat."

Now override the :meth:`~Command.run` method, adding the code you want the bot to run when the command is called.

To send a message in the chat the command was called in, you can use the :meth:`~CommandData.reply` coroutine: ::

    import royalnet.commands as rc

    class SpaghettiCommand(rc.Command):
        name = "spaghetti"

        description = "Send a spaghetti emoji in the chat."

        async def run(self, args: rc.CommandArgs, data: rc.CommandData):
            await data.reply("🍝")

Finally, open the ``commands/__init__.py`` file, and import your command there, then add a reference to your imported
command to the ``available_commands`` list: ::

    # Imports go here!
    from .spaghetti import SpaghettiCommand

    # Enter the commands of your Pack here!
    available_commands = [
        SpaghettiCommand,
    ]

    # Don't change this, it should automatically generate __all__
    __all__ = [command.__name__ for command in available_commands]

Formatting command replies
------------------------------------

You can use a subset of `BBCode <https://en.wikipedia.org/wiki/BBCode>`_ to format messages sent with :meth:`~CommandData.reply`: ::

    async def run(self, args: rc.CommandArgs, data: rc.CommandData):
        await data.reply("[b]Bold of you to assume that my code has no bugs.[/b]")

Available tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's a list of all tags that can be used:

- ``[b]bold[/b]``
- ``[i]italic[/i]``
- ``[c]code[/c]``
- ``[p]multiline \n code[/p]``
- ``[url=https://google.com]inline link[/url]`` (will be rendered differently on every platform)

Command arguments
------------------------------------

A command can have some arguments passed by the user: for example, on Telegram an user may type `/spaghetti carbonara al-dente`
to pass the :class:`str` `"carbonara al-dente"` to the command code.

These arguments can be accessed in multiple ways through the ``args`` parameter passed to the :meth:`~Command.run`
method.

If you want your command to use arguments, override the ``syntax`` class attribute with a brief description of the
syntax of your command, possibly using {curly braces} for required arguments and [square brackets] for optional
ones. ::

    import royalnet.commands as rc

    class SpaghettiCommand(rc.Command):
        name = "spaghetti"

        description = "Send a spaghetti emoji in the chat."

        syntax = "{first_pasta} [second_pasta]"

        async def run(self, args: rc.CommandArgs, data: rc.CommandData):
            first_pasta = args[0]
            second_pasta = args.optional(1)
            if second_pasta is None:
                await data.reply(f"🍝 Here's your {first_pasta}!")
            else:
                await data.reply(f"🍝 Here's your {first_pasta} and your {second_pasta}!")


Direct access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can consider arguments as if they were separated by spaces.

You can then access command arguments directly by number as if the args object was a list of :class:`str`.

If you request an argument with a certain number, but the argument does not exist, an
:exc:`.InvalidInputError` is raised, making the arguments accessed in this way **required**. ::

    args[0]
    # "carbonara"

    args[1]
    # "al-dente"

    args[2]
    # raises InvalidInputError

Optional access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't want arguments to be required, you can access them through the :meth:`~CommandArgs.optional` method: it
will return ``None`` if the argument wasn't passed, making it **optional**. ::

    args.optional(0)
    # "carbonara"

    args.optional(1)
    # "al-dente"

    args.optional(2)
    # None

You can specify a default result too, so that the method will return it instead of returning ``None``: ::

    args.optional(2, default="banana")
    # "banana"

Full string
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want the full argument string, you can use the :meth:`~CommandArgs.joined` method. ::

    args.joined()
    # "carbonara al-dente"

You can specify a minimum number of arguments too, so that an :exc:`.InvalidInputError` will be
raised if not enough arguments are present: ::

    args.joined(require_at_least=3)
    # raises InvalidInputError

Regular expressions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For more complex commands, you may want to get arguments through `regular expressions <https://regexr.com/>`_.

You can then use the :meth:`~CommandArgs.match` method, which tries to match a pattern to the command argument string,
which returns a tuple of the matched groups and raises an :exc:`.InvalidInputError` if there is no match.

To match a pattern, :func:`re.match` is used, meaning that Python will try to match only at the beginning of the string. ::

    args.match(r"(carb\w+)")
    # ("carbonara",)

    args.match(r"(al-\w+)")
    # raises InvalidInputError

    args.match(r"\s*(al-\w+)")
    # ("al-dente",)

    args.match(r"\s*(carb\w+)\s*(al-\w+)")
    # ("carbonara", "al-dente")

Raising errors
---------------------------------------------

If you want to display an error message to the user, you can raise a :exc:`~CommandError` using the error message as argument: ::

    if not kitchen.is_open():
        raise CommandError("The kitchen is closed. Come back later!")

There are some subclasses of :exc:`~CommandError` that can be used for some more specific cases:

:exc:`.UserError`
    The user did something wrong, it is not a problem with the bot.

:exc:`.InvalidInputError`
    The arguments the user passed to the command by the user are invalid.
    *Additionally displays the command syntax in the error message.*

:exc:`.UnsupportedError`
    The command is not supported on the platform it is being called.

:exc:`.ConfigurationError`
    A value is missing or invalid in the ``config.toml`` section of your pack.

:exc:`.ExternalError`
    An external API the command depends on is unavailable or returned an error.

:exc:`.ProgramError`
    An error caused by a programming mistake. Equivalent to :exc:`AssertionError`, but includes a message to facilitate debugging.

Coroutines and slow operations
------------------------------------

You may have noticed that in the previous examples we used ``await data.reply("🍝")`` instead of just ``data.reply("🍝")``.

This is because :meth:`~CommandData.reply` isn't a simple method: it is a coroutine, a special kind of function that
can be executed separately from the rest of the code, allowing the bot to do other things in the meantime.

By adding the ``await`` keyword before the ``data.reply("🍝")``, we tell the bot that it can do other things, like
receiving new messages, while the message is being sent.

You should avoid running slow normal functions inside bot commands, as they will stop the bot from working until they
are finished and may cause bugs in other parts of the code! ::

    async def run(self, args, data):
        # Don't do this!
        image = download_1_terabyte_of_spaghetti("right_now", from="italy")
        ...

If the slow function you want does not cause any side effect, you can wrap it with the :func:`royalnet.utils.asyncify`
function: ::

    async def run(self, args, data):
        # If the called function has no side effect, you can do this!
        image = await asyncify(download_1_terabyte_of_spaghetti, "right_now", from="italy")
        ...

Avoid using :func:`time.sleep` function, as it is considered a slow operation: use instead :func:`asyncio.sleep`,
a coroutine that does the same exact thing but in an asyncronous way.

Delete the invoking message
------------------------------------

The invoking message of a command is the message that the user sent that the bot recognized as a command; for example,
the message ``/spaghetti carbonara`` is the invoking message for the ``spaghetti`` command run.

You can have the bot delete the invoking message for a command by calling the :class:`~CommandData.delete_invoking`
method: ::

    async def run(self, args, data):
        await data.delete_invoking()

Not all platforms support deleting messages; by default, if the platform does not support deletions, the call is
ignored.

You can have the method raise an error if the message can't be deleted by setting the ``error_if_unavailable`` parameter
to True: ::

    async def run(self, args, data):
        try:
            await data.delete_invoking(error_if_unavailable=True)
        except royalnet.error.UnsupportedError:
            await data.reply("🚫 The message could not be deleted.")
        else:
            await data.reply("✅ The message was deleted!")

Sharing data between multiple calls
------------------------------------

The :class:`~Command` class is shared between multiple command calls: if you need to store some data, you may store it as a protected/private field of your command class: ::

    class SpaghettiCommand(rc.Command):
        name = "spaghetti"

        description = "Send a spaghetti emoji in the chat."

        syntax = "(requestedpasta)"

        __total_spaghetti = 0

        async def run(self, args: rc.CommandArgs, data: rc.CommandData):
            self.__total_spaghetti += 1
            await data.reply(f"🍝 Here's your {args[0]}!\n"
                             f"[i]Spaghetti have been served {self.__total_spaghetti} times.[/i]")

Values stored in this way persist **only until the bot is restarted**, and **won't be shared between different serfs**; if you need persistent values, it is recommended to use a database through the Alchemy service.

Using the Alchemy
------------------------------------

Royalnet can be connected to a PostgreSQL database through a special SQLAlchemy interface called
:class:`royalnet.alchemy.Alchemy`.

If the connection is established, the ``self.alchemy`` and ``data.session`` fields will be
available for use in commands.

``self.alchemy`` is an instance of :class:`royalnet.alchemy.Alchemy`, which contains the
:class:`sqlalchemy.engine.Engine`, metadata and tables, while ``data.session`` is a
:class:`sqlalchemy.orm.session.Session`, and can be interacted in the same way as one.

Querying the database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can :class:`sqlalchemy.orm.query.Query` the database using the SQLAlchemy ORM.

The SQLAlchemy tables can be found inside :class:`royalnet.alchemy.Alchemy` with the :meth:`royalnet.alchemy.Alchemy.get` method: ::

    import royalnet.backpack.tables as rbt
    User = self.alchemy.get(rbt.User)

Adding filters to the query
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can filter the query results with the :meth:`sqlalchemy.orm.query.Query.filter` method.

.. note:: Remember to always use a table column as first comparision element, as it won't work otherwise.

::

    query = query.filter(User.role == "Member")


Ordering the results of a query
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can order the query results in **ascending order** with the :meth:`sqlalchemy.orm.query.Query.order_by` method. ::

    query = query.order_by(User.username)

Additionally, you can append the `.desc()` method to a table column to sort in **descending order**: ::

    query = query.order_by(User.username.desc())

Fetching the results of a query
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can fetch the query results with the :meth:`sqlalchemy.orm.query.Query.all`,
:meth:`sqlalchemy.orm.query.Query.first`, :meth:`sqlalchemy.orm.query.Query.one` and
:meth:`sqlalchemy.orm.query.Query.one_or_none` methods.

Remember to use :func:`royalnet.utils.asyncify` when fetching results, as it may take a while!

Use :meth:`sqlalchemy.orm.query.Query.all` if you want a :class:`list` of **all results**: ::

    results: list = await asyncify(query.all)

Use :meth:`sqlalchemy.orm.query.Query.first` if you want **the first result** of the list, or ``None`` if
there are no results: ::

    result: typing.Union[..., None] = await asyncify(query.first)

Use :meth:`sqlalchemy.orm.query.Query.one` if you expect to have **a single result**, and you want the command to
raise an error if any different number of results is returned: ::

    result: ... = await asyncify(query.one)  # Raises an error if there are no results or more than a result.

Use :meth:`sqlalchemy.orm.query.Query.one_or_none` if you expect to have **a single result**, or **nothing**, and
if you want the command to raise an error if the number of results is greater than one. ::

    result: typing.Union[..., None] = await asyncify(query.one_or_none)  # Raises an error if there is more than a result.

More Alchemy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can read more about sqlalchemy at their `website <https://www.sqlalchemy.org/>`_.

Calling Events
------------------------------------

You can **call an event** from inside a command, and receive its return value.

This may be used for example to get data from a different platform, such as getting the users online in a specific Discord server.

You can call an event with the :meth:`.Serf.call_herald_event` method: ::

    result = await self.serf.call_herald_event("event_name")

You can also pass parameters to the called event: ::

    result = await self.serf.call_herald_event("event_name", ..., kwarg=..., *..., **...)

Errors raised by the event will also be raised by the :meth:`.Serf.call_herald_event` method as one of the exceptions described in the :ref:`Raising errors` section.

Distinguish between platforms
------------------------------------

To see if a command is being run on a specific platform, you can check the type of the ``self.serf`` object: ::

    import royalnet.serf.telegram as rst
    import royalnet.serf.discord as rsd
    ...

    if isinstance(self.serf, rst.TelegramSerf):
        await data.reply("This command is being run on Telegram.")
    elif isinstance(self.serf, rsd.DiscordSerf):
        await data.reply("This command is being run on Discord.")
    ...

Displaying Keyboards
------------------------------------

A keyboard is a message with multiple buttons ("keys") attached which can be pressed by an user viewing the message.

Once a button is pressed, a callback function is run, which has its own :class:`~CommandData` context and can do everything a regular comment call could.

The callback function is a coroutine accepting a single ``data: CommandData`` argument: ::

    async def answer(data: CommandData) -> None:
        await data.reply("Spaghetti were ejected from your floppy drive!")

To create a new key, you can use the :class:`~KeyboardKey` class: ::

    key = KeyboardKey(
        short="⏏️",  # An emoji representing the key on platforms the full message cannot be displayed
        text="Eject spaghetti from the floppy drive",  # The text displayed on the key
        callback=answer  # The coroutine to call when the key is pressed.
    )

To display a keyboard and wait for a keyboard press, you can use the :meth:`~CommandData.keyboard` asynccontextmanager.
While the contextmanager is in scope, the keyboard will be valid and it will be possible to interact with it.
Any further key pressed will be answered with an error message. ::

    async with data.keyboard(text="What kind of spaghetti would you want to order?", keys=keyboard):
        # This will keep the keyboard valid for 10 seconds
        await asyncio.sleep(10)

Replies in callbacks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calls to :meth:`~CommandData.reply` made with the :class:`~CommandData` of a keyboard callback won't always result in a message being sent: for example, on Telegram, replies will result in a small message being displayed on the top of the screen.

Reading data from the configuration file
---------------------------------------------

You can read data from your pack's configuration section through the :attr:`~Command.config` attribute: ::

    [Packs."spaghettipack"]
    spaghetti = { mode="al_dente", two=true }

::

    await data.reply(f"Here's your spaghetti {self.config['spaghetti']['mode']}!")

Running code on Serf start
----------------------------------------------

The code inside ``__init__`` is run only once, during the initialization step of the bot: ::

    def __init__(self, serf: "Serf", config):
        super().__init__(serf=serf, config=config)

        # The contents of this variable will be persisted across command calls
        self.persistent_variable = 0

        # The text will be printed only if the config flag is set to something
        if config["spaghetti"]["two"]:
            print("Famme due spaghi!")

.. note:: Some methods may be unavailable during the initialization of the Serf.

Running repeating jobs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To run a job independently from the rest of the command, you can schedule the execution of a coroutine inside ``__init__``: ::

    async def mycoroutine():
        while True:
            print("Free spaghetti every 60 seconds!")
            await asyncio.sleep(60)

    def __init__(self, serf: "Serf", config):
        super().__init__(serf=serf, config=config)
        self.loop.create_task(mycoroutine())

As it will be executed once for every platform Royalnet is running on, you may want to run the task only on a single platform: ::

    def __init__(self, serf: "Serf", config):
        super().__init__(serf=serf, config=config)
        if isinstance(self.serf, rst.TelegramSerf):
            self.loop.create_task(mycoroutine())

