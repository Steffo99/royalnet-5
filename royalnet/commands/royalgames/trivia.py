import typing
import asyncio
import aiohttp
import random
import uuid
from ..command import Command
from ..commandargs import CommandArgs
from ..commanddata import CommandData
from ..commandinterface import CommandInterface
from ...error import *


class TriviaCommand(Command):
    name: str = "trivia"

    description: str = "Manda una domanda dell'OpenTDB in chat."

    _letter_emojis = ["🇦", "🇧", "🇨", "🇩"]

    _correct_emoji = "✅"

    _wrong_emoji = "❌"

    _answer_time = 15

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        self._answerers: typing.Dict[uuid.UUID, typing.Dict[..., bool]] = {}

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        # Fetch the question
        async with aiohttp.ClientSession() as session:
            async with session.get("https://opentdb.com/api.php?amount=1") as response:
                j = await response.json()
        # Parse the question
        if j["response_code"] != 0:
            raise ExternalError(f"OpenTDB returned {j['response_code']} response_code")
        question = j["results"][0]
        text = f'❓ [b]{question["category"]} - {question["difficulty"].capitalize()}[/b]\n' \
               f'{question["question"]}'
        # Prepare answers
        correct_answer: str = question["correct_answer"]
        wrong_answers: typing.List[str] = question["incorrect_answers"]
        answers = [correct_answer, *wrong_answers]
        random.shuffle(answers)
        # Find the correct index
        for index, answer in enumerate(answers):
            if answer == correct_answer:
                correct_index = index
                break
        else:
            raise ValueError("correct_index not found")
        # Add emojis
        for index, answer in enumerate(answers):
            answers[index] = f"{self._letter_emojis[index]} {answers[index]}"
        # Create the question id
        question_id = uuid.uuid4()
        self._answerers[question_id] = {}

        # Create the correct and wrong functions
        async def correct(data: CommandData):
            answerer_ = await data.get_author(error_if_none=True)
            try:
                self._answerers[question_id][answerer_] = True
            except KeyError:
                raise KeyboardExpiredError("Question time ran out.")
            return "🆗 Hai risposto alla domanda. Ora aspetta un attimo per i risultati!"

        async def wrong(data: CommandData):
            answerer_ = await data.get_author(error_if_none=True)
            try:
                self._answerers[question_id][answerer_] = False
            except KeyError:
                raise KeyboardExpiredError("Question time ran out.")
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
        for answerer in self._answerers[question_id]:
            if self._answerers[question_id][answerer]:
                results += self._correct_emoji
            else:
                results += self._wrong_emoji
            results += f" {answerer}\n"
        await data.reply(results)
        del self._answerers[question_id]
