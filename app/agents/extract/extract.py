#
# Extracts list from text
#

import json

from app.llm import ChatModel
from jinja2 import Environment, BaseLoader

GIVE_ME_LIST_PROMPT = open("app/agents/extract/list.prompt.jinja2", "r").read().strip()


class GiveMeList:
    def __init__(self, chat_model: ChatModel, language: str):
        self.chat_model = chat_model
        self.language = language

    def render(
            self, context: str
    ) -> str:
        env = Environment(loader=BaseLoader())
        template = env.from_string(GIVE_ME_LIST_PROMPT)
        return template.render(
            context=context,
            language=self.language,
        )

    def validate_response(self, response: str) -> list[str] | None:
        response = response.strip().replace("```json", "```")

        if response.startswith("```") and response.endswith("```"):
            response = response[3:-3].strip()

        try:
            response = json.loads(response)
        except Exception as _:
            return None

        if "list" not in response:
            return None
        else:
            return response["list"]

    def execute(self, context: str) -> list[str]:
        prompt = self.render(context)
        response = self.chat_model.inference(prompt)

        valid_response: list[str] | None = self.validate_response(response)

        while valid_response is None:
            print("Invalid response from the model, trying again...")
            return self.execute(context)

        return valid_response
