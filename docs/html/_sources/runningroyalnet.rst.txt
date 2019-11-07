.. currentmodule:: royalnet

Running Royalnet
====================================

To run a ``royalnet`` instance, you have first to download the package from ``pip``:

The Keyring
------------------------------------
::

    pip install royalnet


To run ``royalnet``, you'll have to setup the system keyring.

On Windows and desktop Linux, this is already configured;
on a headless Linux instance, you'll need to `manually start and unlock the keyring daemon
<https://keyring.readthedocs.io/en/latest/#using-keyring-on-headless-linux-systems>`_.

Now you have to create a new ``royalnet`` configuration. Start the configuration wizard: ::

    python -m royalnet.configurator

You'll be prompted to enter a "secrets name": this is the name of the group of API keys that will be associated with
your bot. Enter a name that you'll be able to remember. ::

    Desired secrets name [__default__]: royalgames

You'll then be asked for a network password.

This password is used to connect to the rest of the :py:mod:`royalnet.network`, or, if you're hosting a local Network,
it will be the necessary password to connect to it: ::

    Network password []: cosafaunapesuunafoglia

Then you'll be asked for a Telegram Bot API token.
You can get one from `@BotFather <https://t.me/BotFather>`_. ::

    Telegram Bot API token []: 000000000:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA

The next prompt will ask for a Discord Bot API token.
You can get one at the `Discord Developers Portal <https://discordapp.com/developers/applications/>`_. ::

    Discord Bot API token []: AAAAAAAAAAAAAAAAAAAAAAAA.AAAAAA.AAAAAAAAAAAAAAAAAAAAAAAAAAA

Now the configurator will ask you for a Imgur API token.
`Register an application <https://api.imgur.com/oauth2/addclient>`_ on Imgur to be supplied one.
The token should be of type "anonymous usage without user authorization". ::

    Imgur API token []: aaaaaaaaaaaaaaa

Next, you'll be asked for a Sentry DSN. You probably won't have one, so just ignore it and press enter. ::

    Sentry DSN []:

Now that all tokens are configured, you're ready to launch the bot!

Running the bots
------------------------------------

You can run the main ``royalnet`` process by running: ::

    python3.7 -m royalnet

To see all available options, you can run: ::

    python3.7 -m royalnet --help

.. note:: All royalnet options should be specified **after** the word ``royalnet``, or else they will be passed to
          the Python interpreter.

