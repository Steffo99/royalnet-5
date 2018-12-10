# Royalnet

This software is meant for a private internet community, therefore it contains many inside jokes and memes. Be warned!

## Modules

- `bots.py`: Auto-restarting of crashed modules.
- `cast.py`: Magic spell generation (/cast Telegram command)
- `db.py`: PostgreSQL+SQLAlchemy database connection
- `discordbot.py`: [Discord](https://discordapp.com/) music (and more) bot
- `errors.py`: Exception classes for all modules
- `loldata.py`: [League of Legends](https://euw.leagueoflegends.com/) Champion data obtained from [Data Dragon](https://developer.riotgames.com/static-data.html) (may require occasional updates, for example when new champions are released)
- `newuser.py`: _(broken)_ New user creation wizard
- `query_discord_music.py`: Big SQL queries
- `redditbot.py`: reddit bot for [/r/RoyalGames](https://reddit.com/r/RoyalGames)
- `stagismo.py`: Dictionary of words and memes beginning with **S**
- `statsupdate.py`: Game data tracking (Dota, LoL...)
- `telegrambot.py`: [Telegram](https://web.telegram.org/) [multipurpose bot](https://t.me/royalgamesbot)
- `update.sh`: Quick updater script
- `webserver.sh`: [Main](https://ryg.steffo.eu/) webserver for Royalnet

## Install

1. Download `python3.6+`, `sentry-cli` and `ffmpeg` (or `avconv`).
2. Clone the repository.
3. Rename the `template_config.ini` to `config.ini`.
4. Set the correct values in `config.ini`.
5. Add `SENTRY_AUTH_TOKEN=` and `SENTRY_ORG=` to `~/.sentryclirc`.
6. Open a new `screen` and there run `./update.sh`.
7. Detatch the screen with `Ctrl+A` and `Ctrl+D`.

