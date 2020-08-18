# `royalnet` [![PyPI](https://img.shields.io/pypi/v/royalnet.svg)](https://pypi.org/project/royalnet/)

A framework for small Internet communities

## About Royalnet

`royalnet` is a Python framework composed of many interconnected services that may be useful to small Internet communities (gaming clans, university groups, etc).

### [Serfs](royalnet/serf)

_Serfs_ are services that allow Royalnet to respond to **chat commands** on multiple chat platforms.

Commands using the Royalnet Serf API share their code between chat platforms: each serf will handle the specifics for their respective platform, preventing potential bugs due to code duplication!

#### Supported chat platforms

- [Telegram](https://core.telegram.org/bots)
- [Discord](https://discordapp.com/developers/docs/)

More can easily be added by implementing a new serf!

### [Alchemy](royalnet/alchemy)

The _Alchemy_ module allows all Royalnet services to use a **PostgreSQL database** with a [SQLAlchemy](https://www.sqlalchemy.org/) interface.

This allows the usage of a shared and easy-to-use ORM: Alchemy handles for you everything, from the creation of new tables to isolating in transactions the calls made from a Serf command to the database.

### [Herald Network](royalnet/herald)

All Royalnet services can communicate with each other through the _Herald Network_, a websockets-based system allowing Remote Procedure Calls ("_events_") between services.
 
For example, in response to a Telegram message, the Telegram Serf can contact the Discord Serf to ask it to connect to voice chat in Discord. 

Connections between different hosts are possible too, even if they currently are unused by the Royalnet Launcher.

### [Constellation](royalnet/constellation)

The Constellation service is a [Starlette](https://www.starlette.io )-based webserver that can supply dynamic pages ("_stars_") while being connected to the other parts of Royalnet through the Herald.

#### APIs

The Constellation service also offers utilities for creating REST APIs as Python functions with `dict`s as inputs and outputs, leaving (de)serialization, transmission and eventually authentication to Royalnet.

### Sentry

Royalnet can automatically report uncaught errors in all services to a [Sentry](https://sentry.io )-compatible server, while logging them in the console in development environments to facilitate debugging.

### Packs

New Serf _commands_, Constellation _stars_, Herald _events_ and Alchemy _tables_ can be added to Royalnet through plugins called "Packs" that can be activated or deactivated on each single instance.

#### Config

Each pack can access only its individual section in the configuration file, preventing key conflicts (as long as the packs themselves don't share the same name). 

#### Template

New packs can be created starting from [this GitHub template](https://github.com/Steffo99/royalnet-pack-template).

## Installing Royalnet

To install `royalnet`, run:
```
pip install royalnet
```

To install a specific module, run:
```
pip install royalnet[MODULENAME]
```

To install all `royalnet` modules, run:
```
pip install royalnet[telegram,discord,matrix,alchemy_easy,bard,constellation,sentry,herald,coloredlogs]
```

## Documentation

A work-in-progress documentation is available [here](https://gh.steffo.eu/royalnet/html).

## Developing for Royalnet

To develop for `royalnet`, you need to have [Poetry](https://poetry.eustace.io/) installed on your PC.

After you've installed Poetry, clone the git repo with the command:

```
git clone https://github.com/Steffo99/royalnet
```

Then enter the new directory:

```
cd royalnet
```

And finally install all dependencies and the package:

```
poetry install -E telegram -E discord -E matrix -E alchemy_easy -E constellation -E sentry -E herald -E coloredlogs
```

## Help!

Need help in anything Royalnet-related? [Open a issue on GitHub!](https://github.com/Steffo99/royalnet/issues/new)
