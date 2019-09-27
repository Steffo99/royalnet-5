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
---------------------------------------------

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

Delete the invoking message
------------------------------------

The invoking message of a command is the message that the user sent that the bot recognized as a command; for example,
the message ``/spaghetti carbonara`` is the invoking message for the ``spaghetti`` command run.

You can have the bot delete the invoking message for a command by calling the :py:class:`CommandData.delete_invoking`
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
:py:class:`royalnet.database.Alchemy`.

If the connection is established, the ``self.interface.alchemy`` and ``self.interface.session`` fields will be
available for use in commands.

``self.interface.alchemy`` is an instance of :py:class:`royalnet.database.Alchemy`, which contains the
:py:class:`sqlalchemy.engine.Engine`, metadata and tables, while ``self.interface.session`` is a
:py:class:`sqlalchemy.orm.session.Session`, and can be interacted in the same way as one.

If you want to use :py:class:`royalnet.database.Alchemy` in your command, you should override the
``require_alchemy_tables`` field with the :py:class:`set` of Alchemy tables you need. ::

    from royalnet.commands import Command
    from royalnet.database.tables import Royal

    class SpaghettiCommand(Command):
        name = "spaghetti"

        description = "Send a spaghetti emoji in the chat."

        syntax = "(pasta)"

        requrire_alchemy_tables = {Royal}

        ...

Querying the database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can :py:class:`sqlalchemy.orm.query.Query` the database using the SQLAlchemy ORM.

The SQLAlchemy tables can be found inside :py:class:`royalnet.database.Alchemy` with the same name they were created
from, if they were specified in ``require_alchemy_tables``. ::

    RoyalTable = self.interface.alchemy.Royal
    query = self.interface.session.query(RoyalTable)

Adding filters to the query
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can filter the query results with the :py:meth:`sqlalchemy.orm.query.Query.filter` method.

.. note:: Remember to always use a table column as first comparision element, as it won't work otherwise.

::

    query = query.filter(RoyalTable.role == "Member")


Ordering the results of a query
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can order the query results in **ascending order** with the :py:meth:`sqlalchemy.orm.query.Query.order_by` method. ::

    query = query.order_by(RoyalTable.username)

Additionally, you can append the `.desc()` method to a table column to sort in **descending order**: ::

    query = query.order_by(RoyalTable.username.desc())

Fetching the results of a query
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can fetch the query results with the :py:meth:`sqlalchemy.orm.query.Query.all`,
:py:meth:`sqlalchemy.orm.query.Query.first`, :py:meth:`sqlalchemy.orm.query.Query.one` and
:py:meth:`sqlalchemy.orm.query.Query.one_or_none` methods.

Remember to use :py:func:`royalnet.utils.asyncify` when fetching results, as it may take a while!

Use :py:meth:`sqlalchemy.orm.query.Query.all` if you want a :py:class:`list` of **all results**: ::

    results: list = await asyncify(query.all)

Use :py:meth:`sqlalchemy.orm.query.Query.first` if you want **the first result** of the list, or :py:const:`None` if
there are no results: ::

    result: typing.Union[..., None] = await asyncify(query.first)

Use :py:meth:`sqlalchemy.orm.query.Query.one` if you expect to have **a single result**, and you want the command to
raise an error if any different number of results is returned: ::

    result: ... = await asyncify(query.one)  # Raises an error if there are no results or more than a result.

Use :py:meth:`sqlalchemy.orm.query.Query.one_or_none` if you expect to have **a single result**, or **nothing**, and
if you want the command to raise an error if the number of results is greater than one. ::

    result: typing.Union[..., None] = await asyncify(query.one_or_none)  # Raises an error if there is more than a result.

More Alchemy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can read more about :py:mod:`sqlalchemy` at their `website <https://www.sqlalchemy.org/>`_.

Comunicating via Royalnet
------------------------------------

This section will be changed soon; as such, it will not be documented.
