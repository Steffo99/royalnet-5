# `royalnet` [![PyPI](https://img.shields.io/pypi/v/royalnet.svg)](https://pypi.org/project/royalnet/)

A multipurpose bot framework and webserver

## About

`royalnet` is a Python framework that allows you to create interconnected modular chat bots accessible through multiple interfaces (such as Telegram or Discord), and also modular websites that can be connected with the bots.

### Supported bot platforms ("serfs")

- [Telegram](https://core.telegram.org/bots)
- [Discord](https://discordapp.com/developers/docs/)
- [Matrix](https://matrix.org/) (no E2E support yet)

## Installing

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

`royalnet`'s documentation is available [here](https://gh.steffo.eu/royalnet).

## Developing `royalnet`

To develop `royalnet`, you need to have [Poetry](https://poetry.eustace.io/) installed on your PC.

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
poetry install -E telegram -E discord -E matrix -E alchemy_easy -E bard -E constellation -E sentry -E herald -E coloredlogs
```