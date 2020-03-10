Creating a new Pack
====================================

Prerequisites
------------------------------------

You'll need to have `Python 3.8 <https://www.python.org/downloads/release/python-382/>`_ and `poetry <https://github.com/python-poetry/poetry>`_
to develop Royalnet Packs.

Creating the repository
------------------------------------

To create a new pack, create a new repository based on the `Royalnet Pack template <https://github.com/Steffo99/royalnet-pack-template>`_
and clone it to your workspace.

pyproject.toml
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``pyproject.toml`` file contains information about your Python project that will be read by ``poetry`` while building
the pack and publishing it to PyPI.

Choose a name for your Pack and set it in the ``tool.property.name`` field: ::

    [tool.poetry]
        # TODO: Insert here your Pack name!
        name = "pastapack"
        # ...

Follow the instructions in the other ``# TODO`` comments to finish editing the file.

examplepack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``examplepack`` folder contains the source code of your pack, and should be renamed to the name you set in the ``pyproject.toml`` file.

It should contain a ``version.py`` file and six folders: ::

    examplepack
    ├── commands
    ├── events
    ├── stars
    ├── tables
    ├── types
    ├── utils
    └── version.py

version.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``version.py`` file contains the version number of your pack.

If you changed the ``version`` field in the ``pyproject.toml`` file, change the value of ``semantic`` in ``version.py`` to the same value.

Remember to use `semantic versioning <https://semver.org/>`_! ::

    semantic = "1.0.0"

The commands folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The commands folder should contain all commands that your Pack will add to the Royalnet instances it is installed in.

To learn how to create a new :class:`~commands.Command`, read the :doc:`command` page.

The events folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The events folder should contain all events (remote procedure calls) that your Pack will add to the Royalnet instances it is installed in.

To learn how to create a new :class:`~commands.Event`, read the :doc:`event` page.

The stars folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The stars folder should contain all stars (webserver routes) that your Pack will add to the Royalnet instances it is installed in.

To learn how to create a new :class:`~constellation.PageStar`, read the :doc:`star` page.

The tables folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The tables folder should contain all Alchemy tables (SQLAlchemy-compatible SQL tables) that your Pack will add to the Royalnet instances it is installed in.

To learn how to create a new table, read the :doc:`table` page.

The utils folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The utils folder should contain the utility functions and classes that your Pack uses.

Its contents are imported **before** the commands, events and stars but **after** the tables, so **you can't import them** in the files contained in the ``tables`` folder, or you will create a `circular import <https://stackabuse.com/python-circular-imports/>`_!

Files in this folder are **forbidden from importing modules** from the ``commands``, ``events`` and ``stars`` folders, as that will create a circular import too.

The types folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The types folder should contain the enums and custom types that are used in your tables.

Please note that the contents of this folder are imported **before** everything else in the pack.

Its contents **can be imported anywhere** in the Pack, including the ``tables`` folder, without creating a circular import.

However, its files are **forbidden from importing anything else** from the rest of the pack!

Publishing the pack
------------------------------------

This section is not documented yet.
