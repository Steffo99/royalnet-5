import utils
import dice
import typing


class SafeDict(dict):
    def __missing__(self, key):
        return key


def safely_format_string(string: str, words: typing.Dict[str, str] = None, ignore_escaping=False) -> str:
    if words is None:
        words = {}
    if ignore_escaping:
        escaped = words
    else:
        escaped = {}
        for key in words:
            escaped[key] = words[key].replace("<", "&lt;").replace(">", "&gt;")
    return string.format_map(SafeDict(**escaped))


# Generic telegram errors
class TELEGRAM:
    BOT_STARTED = "✅ Hai autorizzato il bot ad inviarti messaggi privati."

    class ERRORS:
        CRITICAL_ERROR = "☢ <b>ERRORE CRITICO!</b>\nIl bot ha ignorato il comando.\nUna segnalazione di errore è stata automaticamente mandata a @Steffo.\n\nDettagli dell'errore:\n<pre>{exc_info}</pre>"
        UNAUTHORIZED_USER = "⚠ Non sono autorizzato a inviare messaggi a {mention}.\nPer piacere, {mention}, inviami un messaggio in privata!"
        UNAUTHORIZED_GROUP = "⚠ Non sono autorizzato a inviare messaggi in <i>{group}</i>.\n@Steffo, aggiungimi al gruppo o concedimi i permessi!"


PONG = "🏓 Pong!"


# Ah, non lo so io.
class AHNONLOSOIO:
    ONCE = "😐 Ah, non lo so io!"
    AGAIN = "😐 Ah, non lo so nemmeno io..."


# Bridge commands between Discord and Telegram
class BRIDGE:
    SUCCESS = "✅ Comando inoltrato a Discord."
    FAILURE = "❎ Errore nell'esecuzione del comando su Discord."

    class ERRORS:
        INVALID_SYNTAX = "⚠ Non hai specificato un comando!\nSintassi: <code>/bridge (comando)</code>"
        INACTIVE_BRIDGE = "⚠ Il collegamento tra Telegram e Discord non è attivo al momento."


# Random spellslinging
class CAST:
    class ERRORS:
        NOT_YET_AVAILABLE = "⚠ Il nuovo cast non è ancora disponibile! Per un'anteprima sulle nuove funzioni, usa <code>/spell</code>."


# Ciao Ruozi!
class CIAORUOZI:
    THE_LEGEND_HIMSELF = "👋 Ciao me!"
    SOMEBODY_ELSE = "👋 Ciao Ruozi!"


# The /color meme, from Octeon
COLOR = "<i>I am sorry, unknown error occured during working with your request, Admin were notified</i>"


# Diario
class DIARIO:
    SUCCESS = "✅ Riga aggiunta al diario:\n{diario}"

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
    FOODS = {
        "_default": "🍗 Hai mangiato {food}!\n<i>Ma non succede nulla.</i>",
        "tonnuooooooro": "👻 Il {food} che hai mangiato era posseduto.\n<i>Spooky!</i>",
        "uranio": "☢️ L'{food} che hai mangiato era radioattivo.\n<i>Stai brillando di verde!</i>",
        "pollo": '🍗 Il {food} che hai appena mangiato proveniva <a href="https://store.steampowered.com/app/353090/Chicken_Invaders_5/">dallo spazio</a>.\n<i>Coccodè?</i>',
        "ragno": "🕸 Hai mangiato un {food}.\n<i>Ewww!</i>",
        "curry": "🔥 BRUCIAAAAAAAAAA! Il {food} era piccantissimo!\n<i>Stai sputando fiamme!</i>",
        "torta": "⬜️ Non hai mangiato niente.\n<i>La {food} è una menzogna!</i>",
        "cake": "⬜️ Non hai mangiato niente.\n<i>The {food} is a lie!</i>",
        "biscotto": "🍪 Hai mangiato un {food} di contrabbando.\n<i>L'Inquisizione non lo saprà mai!</i>",
        "biscotti": "🍪 Hai mangiato tanti {food} di contrabbando.\n<i>Attento! L'Inquisizione è sulle tue tracce!</i>",
        "tango": "🌳 Hai mangiato un {food}, e un albero insieme ad esso.\n<i>Senti il tuo corpo curare le tue ferite.</i>",
        "sasso": "🥌 Il {food} che hai mangiato era duro come un {food}\n<i>Stai soffrendo di indigestione!</i>"
    }

    class ERRORS:
        INVALID_SYNTAX = "⚠ Non hai specificato cosa mangiare!\nSintassi: <code>/eat (cibo)</code>"


# Royalnet linking
class LINK:
    SUCCESS = "✅ Collegamento riuscito!"

    class ERRORS:
        INVALID_SYNTAX = "⚠ Non hai specificato un username!\nSintassi: <code>/link (username)</code>"
        NOT_FOUND = "⚠ Non esiste nessun account Royalnet con quel nome.\nNota: gli username sono case-sensitive, e iniziano sempre con una maiuscola!"
        ALREADY_EXISTING = "⚠ Questo account è già collegato a un account Royalnet."
        ROYALNET_NOT_LINKED = "⚠ Il tuo account Telegram non è connesso a Royalnet! Connettilo con <code>/link (username)</code>."


# Markov strings
class MARKOV:
    class ERRORS:
        NO_MODEL = "⚠ La catena di Markov non è disponibile."
        GENERATION_FAILED = "⚠ <code>markovify</code> non è riuscito a generare una frase. Prova di nuovo?\n E' un'avvenimento sorprendentemente raro..."
        SPECIFIC_WORD_FAILED = "⚠ <code>markovify</code> non è riuscito a generare una frase partendo da questa parola. Provane una diversa..."
        MISSING_WORD = "⚠ La parola specificata non è presente nella catena di Markov. Provane una diversa..."


# Matchmaking service strings
class MATCHMAKING:
    EMOJIS = {
        "ready": "🔵",
        "wait_for_me": "🕒",
        "maybe": "❓",
        "ignore": "❌",
        "close": "🚩",
        "cancel": "🗑"
    }

    ENUM_TO_EMOJIS = {
        utils.MatchmakingStatus.READY: EMOJIS["ready"],
        utils.MatchmakingStatus.WAIT_FOR_ME: EMOJIS["wait_for_me"],
        utils.MatchmakingStatus.MAYBE: EMOJIS["maybe"],
        utils.MatchmakingStatus.IGNORED: EMOJIS["ignore"],
    }

    BUTTONS = {
        "match_ready": f"{EMOJIS['ready']} Sono pronto per iniziare!",
        "match_wait_for_me": f"{EMOJIS['wait_for_me']} Ci sarò, aspettatemi!",
        "match_maybe": f"{EMOJIS['maybe']} Forse vengo, se non ci sono fate senza di me.",
        "match_ignore": f"{EMOJIS['ignore']} Non ci sarò.",
        "match_close": f"{EMOJIS['close']} ADMIN: Avvia la partita",
        "match_cancel": f"{EMOJIS['cancel']} ADMIN: Annulla la partita"
    }

    TICKER_TEXT = {
        "match_ready": f"{EMOJIS['ready']} Hai detto che sei pronto per giocare!",
        "match_wait_for_me": f"{EMOJIS['wait_for_me']} Hai chiesto agli altri di aspettarti.",
        "match_maybe": f"{EMOJIS['maybe']} Hai detto che forse ci sarai.",
        "match_ignore": f"{EMOJIS['ignore']} Non hai intenzione di partecipare.",
        "match_close": f"{EMOJIS['close']} Hai notificato tutti che la partita sta iniziando.",
        "match_cancel": f"{EMOJIS['cancel']} Hai annullato la partita."
    }

    GAME_START = {
        int(utils.MatchmakingStatus.READY): "🔵 Che <b>{match_title}</b> abbia inizio!",
        int(utils.MatchmakingStatus.WAIT_FOR_ME): "🕒 Sbrigati! <b>{match_title}</b> sta per iniziare!",
        int(utils.MatchmakingStatus.MAYBE): "❓ <b>{match_title}</b> sta iniziando. Se vuoi partecipare, fai in fretta!",
    }

    class ERRORS:
        INVALID_SYNTAX = "⚠ Sintassi del comando errata.\nSintassi: <pre>/mm [minplayers-][maxplayers] ['per'] (gamename) \\n[descrizione]</pre>"
        NOT_ADMIN = "⚠ Non sei il creatore di questo match!"
        MATCH_CLOSED = "⚠ Il matchmaking per questa partita è terminato."


# Dice roller
class ROLL:
    SUCCESS = "🎲 {result}"

    SYMBOLS = {
        dice.elements.Div: "/",
        dice.elements.Mul: "*",
        dice.elements.Sub: "-",
        dice.elements.Add: "+",
        dice.elements.Modulo: "%",
        dice.elements.AddEvenSubOdd: "+-",
        dice.elements.Highest: "h",
        dice.elements.Lowest: "l",
        dice.elements.Middle: "m",
        dice.elements.Again: "a",
        dice.elements.Successes: "e",
        dice.elements.SuccessFail: "f",
        dice.elements.ArrayAdd: ".+",
        dice.elements.ArraySub: ".-",
        dice.elements.Array: ",",
        dice.elements.Extend: "|",
        dice.elements.Reroll: "r",
        dice.elements.Explode: "x",
        dice.elements.ForceReroll: "rr"
    }

    class ERRORS:
        INVALID_SYNTAX = "⚠ Sintassi del tiro di dadi non valida."
        DICE_ERROR = "⚠ Il tiro di dadi è fallito."


# Ship creator
class SHIP:
    RESULT = "💕 {one} + {two} = <b>{result}</b>"

    class ERRORS:
        INVALID_SYNTAX = "⚠ Non hai specificato correttamente i due nomi!\nSintassi: <code>/ship (nome) (nome)</code>"
        INVALID_NAMES = "⚠ I nomi specificati non sono validi.\nRiprova con dei nomi diversi!"


# Get information about a spell
class SPELL:
    HEADER = "🔍 La magia <b>{name}</b> ha le seguenti proprietà (v{version}):\n"
    ACCURACY = "Precisione - <b>{accuracy}%</b>\n"
    DAMAGE = "Danni - <b>{number}d{type}{constant}</b>\n"
    TYPE = "Tipo - <b>{type}</b>\n"
    REPEAT = "Multiattacco - <b>×{repeat}</b>\n"

    class ERRORS:
        INVALID_SYNTAX = "⚠ Non hai specificato la magia di cui vuoi conoscere i dettagli!\nSintassi: <code>/spell (nome)</code>"


# Secondo me, è colpa delle stringhe.
SMECDS = "🤔 Secondo me, è colpa {ds}."


# Wiki notifications
class WIKI:
    PAGE_LOCKED = '🔒 La pagina wiki <a href="https://ryg.steffo.eu/wiki/{key}">{key}</a> è stata bloccata da <b>{user}</b>.'
    PAGE_UNLOCKED = '🔓 La pagina wiki <a href="https://ryg.steffo.eu/wiki/{key}">{key}</a> è stata sbloccata da <b>{user}</b>.'
