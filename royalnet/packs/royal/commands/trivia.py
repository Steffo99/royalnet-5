import typing
import asyncio
import aiohttp
import random
import uuid
import html
from royalnet.commands import *
from royalnet.utils import asyncify
from ..tables import TriviaScore


class TriviaCommand(Command):
    name: str = "trivia"

    aliases = ["t"]

    description: str = "Manda una domanda dell'OpenTDB in chat."

    tables = {TriviaScore}

    _letter_emojis = ["🇦", "🇧", "🇨", "🇩"]

    _correct_emoji = "✅"

    _wrong_emoji = "❌"

    _answer_time = 14

    _question_lock: bool = False

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        self._answerers: typing.Dict[uuid.UUID, typing.Dict[str, bool]] = {}

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        if self._question_lock:
            raise CommandError("C'è già un'altra domanda attiva!")
        self._question_lock = True
        # Fetch the question
        async with aiohttp.ClientSession() as session:
            async with session.get("https://opentdb.com/api.php?amount=1") as response:
                j = await response.json()
        # Parse the question
        if j["response_code"] != 0:
            raise CommandError(f"OpenTDB returned an error response_code ({j['response_code']}).")
        question = j["results"][0]
        text = f'❓ [b]{question["category"]} - {question["difficulty"].capitalize()}[/b]\n' \
               f'{html.unescape(question["question"])}'
        # Prepare answers
        correct_answer: str = question["correct_answer"]
        wrong_answers: typing.List[str] = question["incorrect_answers"]
        answers: typing.List[str] = [correct_answer, *wrong_answers]
        if question["type"] == "multiple":
            random.shuffle(answers)
        elif question["type"] == "boolean":
            answers.sort(key=lambda a: a)
            answers.reverse()
        else:
            raise NotImplementedError("Unknown question type")
        # Find the correct index
        for index, answer in enumerate(answers):
            if answer == correct_answer:
                correct_index = index
                break
        else:
            raise ValueError("correct_index not found")
        # Add emojis
        for index, answer in enumerate(answers):
            answers[index] = f"{self._letter_emojis[index]} {html.unescape(answers[index])}"
        # Create the question id
        question_id = uuid.uuid4()
        self._answerers[question_id] = {}

        # Create the correct and wrong functions
        async def correct(data: CommandData):
            answerer_ = await data.get_author(error_if_none=True)
            try:
                self._answerers[question_id][answerer_.uid] = True
            except KeyError:
                raise KeyboardExpiredError("Tempo scaduto!")
            return "🆗 Hai risposto alla domanda. Ora aspetta un attimo per i risultati!"

        async def wrong(data: CommandData):
            answerer_ = await data.get_author(error_if_none=True)
            try:
                self._answerers[question_id][answerer_.uid] = False
            except KeyError:
                raise KeyboardExpiredError("Tempo scaduto!")
            return "🆗 Hai risposto alla domanda. Ora aspetta un attimo per i risultati!"

        # Add question
        keyboard = {}
        for index, answer in enumerate(answers):
            if index == correct_index:
                keyboard[answer] = correct
            else:
                keyboard[answer] = wrong
        await data.keyboard(text, keyboard)
        await asyncio.sleep(self._answer_time)
        results = f"❗️ Tempo scaduto!\n" \
                  f"La risposta corretta era [b]{answers[correct_index]}[/b]!\n\n"
        for answerer_id in self._answerers[question_id]:
            answerer = data.session.query(self.alchemy.User).get(answerer_id)
            if answerer.trivia_score is None:
                ts = self.interface.alchemy.TriviaScore(royal=answerer)
                data.session.add(ts)
                data.session.commit()
            if self._answerers[question_id][answerer_id]:
                results += self._correct_emoji
                answerer.trivia_score.correct_answers += 1
            else:
                results += self._wrong_emoji
                answerer.trivia_score.wrong_answers += 1
            results += f" {answerer} ({answerer.trivia_score.correct_answers}/{answerer.trivia_score.total_answers})\n"
        await data.reply(results)
        del self._answerers[question_id]
        await asyncify(data.session.commit)
        self._question_lock = False
