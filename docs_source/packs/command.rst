.. currentmodule:: royalnet.commands

Creating a new Command
====================================

A Royalnet Command is a small script that is run whenever a specific message is sent to a Royalnet interface.

A Command code looks like this: ::

    import royalnet.commands as rc

    class PingCommand(rc.Command):
        name = "ping"

        description = "Play ping-pong with the bot."

        def __init__(self, interface):
            # This code is run just once, while the bot is starting
            super().__init__()

        async def run(self, args: rc.CommandArgs, data: rc.CommandData):
            # This code is run every time the command is called
            await data.reply("Pong!")

Creating a new Command
------------------------------------

First, think of a ``name`` for your command.
It's the name your command will be called with: for example, the "spaghetti" command will be called by typing **/spaghetti** in chat.
Try to keep the name as short as possible, while staying specific enough so no other command will have the same name.

Next, create a new Python file with the ``name`` you have thought of.
The previously mentioned "spaghetti" command should have a file called ``spaghetti.py``.

Then, in the first row of the file, import the :class:`Command` class from royalnet, and create a new class inheriting from it: ::

    import royalnet.commands as rc

    class SpaghettiCommand(rc.Command):
        ...

Inside the class, override the attributes ``name`` and ``description`` with respectively the **name of the command** and a **small description of what the command will do**: ::

    import royalnet.commands as rc

    class SpaghettiCommand(rc.Command):
        name = "spaghetti"

        description = "Send a spaghetti emoji in the chat."

Now override the :meth:`Command.run` method, adding the code you want the bot to run when the command is called.

To send a message in the chat the command was called in, you can use the :meth:`CommandData.reply` coroutine: ::

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

Command arguments
------------------------------------

A command can have some arguments passed by the user: for example, on Telegram an user may type `/spaghetti carbonara al-dente`
to pass the :class:`str` `"carbonara al-dente"` to the command code.

These arguments can be accessed in multiple ways through the ``args`` parameter passed to the :meth:`Command.run`
method.

If you want your command to use arguments, override the ``syntax`` class attribute with a brief description of the
syntax of your command, possibly using {curly braces} for required arguments and [square brackets] for optional
ones. ::

    import royalnet.commands as rc

    class SpaghettiCommand(rc.Command):
        name = "spaghetti"

        description = "Send a spaghetti emoji in the chat."

        syntax = "(requestedpasta)"

        async def run(self, args: rc.CommandArgs, data: rc.CommandData):
            await data.reply(f"🍝 Here's your {args[0]}!")


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

If you don't want arguments to be required, you can access them through the :meth:`CommandArgs.optional` method: it
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

If you want the full argument string, you can use the :meth:`CommandArgs.joined` method. ::

    args.joined()
    # "carbonara al-dente"

You can specify a minimum number of arguments too, so that an :exc:`.InvalidInputError` will be
raised if not enough arguments are present: ::

    args.joined(require_at_least=3)
    # raises InvalidInputError

Regular expressions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For more complex commands, you may want to get arguments through `regular expressions <https://regexr.com/>`_.

You can then use the :meth:`CommandArgs.match` method, which tries to match a pattern to the command argument string,
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

If you want to display an error message to the user, you can raise a :exc:`.CommandError` using the error message as argument: ::

    if not kitchen.is_open():
        raise CommandError("The kitchen is closed. Come back later!")

There are some subclasses of :exc:`.CommandError` that can be used for some more specific cases:

:exc:`.UserError`
    The user did something wrong, it is not a problem with the bot.

:exc:`.InvalidInputError`
    The arguments the user passed to the command by the user are invalid.
    Displays the command syntax in the error message.

:exc:`.UnsupportedError`
    The command is not supported on the interface it is being called.

:exc:`.ConfigurationError`
    The ``config.toml`` file was misconfigured (a value is missing or invalid).

:exc:`.ExternalError`
    An external API the command depends on is unavailable or returned an error.

:exc:`.ProgramError`
    An error caused by a programming mistake. Equivalent to :exc:`AssertionError`, but includes a message to facilitate debugging.

Coroutines and slow operations
------------------------------------

You may have noticed that in the previous examples we used ``await data.reply("🍝")`` instead of just ``data.reply("🍝")``.

This is because :meth:`CommandData.reply` isn't a simple method: it is a coroutine, a special kind of function that
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

You can have the bot delete the invoking message for a command by calling the :class:`CommandData.delete_invoking`
method: ::

    async def run(self, args, data):
        await data.delete_invoking()

Not all interfaces support deleting messages; by default, if the interface does not support deletions, the call is
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

Using the database
------------------------------------

Bots can be connected to a PostgreSQL database through a special SQLAlchemy interface called
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

This section is not documented yet.

Displaying Keyboards
------------------------------------

This section is not documented yet.

Running code at the initialization of the bot
---------------------------------------------

This section is not documented yet.

Running repeating jobs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section is not documented yet.
