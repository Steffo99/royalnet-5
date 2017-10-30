import multiprocessing
import telegrambot
import discordbot

discord_users_pipe = multiprocessing.Pipe()

discord = multiprocessing.Process(target=discordbot.process, args=(discord_users_pipe[0],))
telegram = multiprocessing.Process(target=telegrambot.process, args=(discord_users_pipe[1],))

if __name__ == "__main__":
    discord.start()
    telegram.start()