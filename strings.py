from db import MatchmakingStatus


class SafeDict(dict):
    def __missing__(self, key):
        return '<code>' + key + '</code>'


def safely_format_string(string, **kwargs):
    return string.format_map(SafeDict(**kwargs))


# Generic telegram errors
class TELEGRAM:
    BOT_STARTED = "✅ Hai autorizzato il bot ad inviarti messaggi privati."

    class ERRORS:
        CRITICAL_ERROR = "☢ <b>ERRORE CRITICO!</b>\nIl bot ha ignorato il comando.\nUna segnalazione di errore è stata automaticamente mandata a @Steffo.\n\nDettagli dell'errore:\n<pre>{exc_info}</pre>"
        TELEGRAM_NOT_LINKED = "⚠ Il tuo account Telegram non è registrato a Royalnet! Registrati con `/register@royalgamesbot <nomeutenteryg>`."


PONG = "🏓 Pong!"


# Royalnet linking
class LINKING:
    SUCCESSFUL = "✅ Collegamento riuscito!"

    class ERRORS:
        INVALID_SYNTAX = "⚠ Non hai specificato un username!\nSintassi del comando: <code>/register {username}</code>"
        NOT_FOUND = "⚠ Non esiste nessun account Royalnet con quel nome."
        ALREADY_EXISTING = "⚠ Questo account è già collegato a un account Royalnet."


# Markov strings
class MARKOV:
    class ERRORS:
        NO_MODEL = "⚠ La catena di Markov non è disponibile."
        GENERATION_FAILED = "⚠ <code>markovify</code> non è riuscito a generare una frase. Prova di nuovo?\n E' un'avvenimento sorprendentemente raro..."
        SPECIFIC_WORD_FAILED = "⚠ <code>markovify</code> non è riuscito a generare una frase partendo da questa parola. Provane una diversa..."
        MISSING_WORD = "⚠ La parola specificata non è presente nella catena di Markov. Provane una diversa..."


# Matchmaking service strings
class MATCHMAKING:
    TICKER_TEXT = {
        "match_ready": "🔵 Hai detto che sei pronto per giocare!",
        "match_wait_for_me": "🕒 Hai chiesto agli altri di aspettarti.",
        "match_maybe": "❔ Hai detto che forse ci sarai.",
        "match_someone_else": "💬 Hai detto che vuoi aspettare che venga qualcun altro.",
        "match_ignore": "❌ Non hai intenzione di partecipare.",
        "match_close": "🚩 Hai notificato tutti che la partita sta iniziando.",
        "match_cancel": "🗑 Hai annullato la partita."
    }

    GAME_START = {
        MatchmakingStatus.READY: "🔵 Che <b>{match_title}</b> abbia inizio!",
        MatchmakingStatus.WAIT_FOR_ME: "🕒 Sbrigati! <b>{match_title}</b> sta per iniziare!",
        MatchmakingStatus.SOMEONE_ELSE: "❔ <b>{match_title}</b> sta iniziando. Se vuoi partecipare, fai in fretta!",
        MatchmakingStatus.MAYBE: "💬 <b>{match_title}</b> sta per iniziare, e ci sono {active_players} giocatori."
    }

    BUTTONS = {
        "match_ready": "🔵 Sono pronto per iniziare!",
        "match_wait_for_me": "🕒 Ci sarò, aspettatemi!",
        "match_maybe": "❔ Forse vengo, se non ci sono fate senza di me.",
        "match_someone_else": "💬 Solo se viene anche qualcun altro...",
        "match_ignore": "❌ Non ci sarò.",
        "match_close": "🚩 ADMIN: Avvia la partita",
        "match_cancel": "🗑 ADMIN: Annulla la partita"
    }

    class ERRORS:
        INVALID_SYNTAX = "⚠ Sintassi del comando errata.\nSintassi: <pre>/mm [minplayers-][maxplayers] per {gamename} \\n[descrizione]</pre>"
        NOT_ADMIN = "⚠ Non sei il creatore di questo match!"
        MATCH_CLOSED = "⚠ Il matchmaking per questa partita è terminato!"
        UNAUTHORIZED = "⚠ Non sono autorizzato a inviare messaggi a {mention}.\nPer piacere, {mention}, inviami un messaggio in privata!"


# Diario search
class DIARIOSEARCH:
    HEADER = "ℹ️ Risultati della ricerca di {term}:\n"

    class ERRORS:
        INVALID_SYNTAX = "⚠ Non hai specificato un termine da cercare!\nSintassi: <pre>/search {termine}</pre>"