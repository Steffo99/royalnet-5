# `royalnet` [![PyPI](https://img.shields.io/pypi/v/royalnet.svg)](https://pypi.org/project/royalnet/)

The fifth rewrite of the Royal Network!

It has a lot of submodules, many of which may be used in other bots.

[Documentation available here](https://royal-games.github.io/royalnet/html/index.html).

## Installation for the Royal Games community

With `python3.7` and `pip` installed, run:

```bash
pip install royalnet
pip install websockets --upgrade
export TG_AK="Telegram API Key"
export DS_AK="Discord API Key"
export DB_PATH="sqlalchemy database path to postgresql"
export MASTER_KEY="A secret password to connect to the network"
python3.7 -m royalnet.royalgames -OO
```
