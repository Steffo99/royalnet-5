from db import MatchmakingStatus
import typing


class SafeDict(dict):
    def __missing__(self, key):
        return key


def safely_format_string(string: str, words: typing.Dict[str, str]) -> str:
    escaped = {}
    for key in words:
        escaped[key] = words[key].replace("<", "&lt;").replace(">", "&gt;")
    return string.format_map(SafeDict(**escaped))


# Generic telegram errors
class TELEGRAM:
    BOT_STARTED = "✅ Hai autorizzato il bot ad inviarti messaggi privati."

    class ERRORS:
        CRITICAL_ERROR = "☢ <b>ERRORE CRITICO!</b>\nIl bot ha ignorato il comando.\nUna segnalazione di errore è stata automaticamente mandata a @Steffo.\n\nDettagli dell'errore:\n<pre>{exc_info}</pre>"
        ROYALNET_NOT_LINKED = "⚠ Il tuo account Telegram non è connesso a Royalnet! Connettilo con <code>/link (NomeUtenteRoyalnet)</code>."
        UNAUTHORIZED_USER = "⚠ Non sono autorizzato a inviare messaggi a {mention}.\nPer piacere, {mention}, inviami un messaggio in privata!"
        UNAUTHORIZED_GROUP = "⚠ Non sono autorizzato a inviare messaggi in <i>{group}</i>.\n@Steffo, aggiungimi al gruppo o concedimi i permessi!"
        INACTIVE_BRIDGE = "⚠ Il collegamento tra Telegram e Discord non è attivo al momento."


PONG = "🏓 Pong!"


# Diario
class DIARIO:
    SUCCESS = "✅ Riga aggiunta al diario:\n{diario}"
    ENTRY = '<a href="https://ryg.steffo.eu/diario#entry-{id}">#{id}</a> di <b>{author}</b>\n{text}'

    class ERRORS:
        INVALID_SYNTAX = "⚠ Sintassi del comando errata.\nSintassi: <code>/diario (frase)</code>, oppure rispondi a un messaggio con <code>/diario</code>."
        NO_TEXT = "⚠ Il messaggio a cui hai risposto non contiene testo."


# Diario search
class DIARIOSEARCH:
    HEADER = "ℹ️ Risultati della ricerca di {term}:\n"

    class ERRORS:
        INVALID_SYNTAX = "⚠ Non hai specificato un termine da cercare!\nSintassi: <code>/{command} (termine)</code>"
        RESULTS_TOO_LONG = "⚠ Sono presenti troppi risultati da visualizzare! Prova a restringere la ricerca."


# Eat!
class EAT:
    NORMAL = "🍗 Hai mangiato {food}!"
    OUIJA = "👻 Il {food} che hai mangiato era posseduto.\nSpooky!"

    class ERRORS:
        INVALID_SYNTAX = "⚠ Non hai specificato cosa mangiare!\nSintassi: <code>/eat (cibo)</code>"


# Royalnet linking
class LINK:
    SUCCESS = "✅ Collegamento riuscito!"

    class ERRORS:
        INVALID_SYNTAX = "⚠ Non hai specificato un username!\nSintassi del comando: <code>/register (NomeUtenteRoyalnet)</code>"
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
        INVALID_SYNTAX = "⚠ Sintassi del comando errata.\nSintassi: <pre>/mm [minplayers-][maxplayers] per (gamename) \\n[descrizione]</pre>"
        NOT_ADMIN = "⚠ Non sei il creatore di questo match!"
        MATCH_CLOSED = "⚠ Il matchmaking per questa partita è terminato!"


# Ship creator
class SHIP:
    RESULT = "💕 {one} + {two} = <b>{result}</b>"

    class ERRORS:
        INVALID_SYNTAX = "⚠ Non hai specificato correttamente i due nomi!\nSintassi corretta: <code>/ship (nome) (nome)</code>"
        INVALID_NAMES = "⚠ I nomi specificati non sono validi.\nRiprova con dei nomi diversi!"


# Wiki notifications
class WIKI:
    PAGE_LOCKED = '🔒 La pagina wiki <a href="https://ryg.steffo.eu/wiki/{key}">{key}</a> è stata bloccata da <b>{user}</b>.'
    PAGE_UNLOCKED = '🔓 La pagina wiki <a href="https://ryg.steffo.eu/wiki/{key}">{key}</a> è stata sbloccata da <b>{user}</b>.'
