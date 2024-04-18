import json
from dataclasses import dataclass
from typing import Optional

from app.llm import ChatModel
from app.logger import Logger
from jinja2 import Environment, BaseLoader

RESEARCH_PROMPT = open("app/agents/investigate/research.prompt.jinja2", "r").read().strip()
INVESTIGATION_PROMPT = open("app/agents/investigate/investigation.prompt.jinja2", "r").read().strip()


@dataclass(frozen=True)
class ResearchResponse:
    draft: str
    action: str


class Research:
    def __init__(self, chat_model: ChatModel, language: str):
        self.logger = Logger()
        self.chat_model = chat_model
        self.language = language

    def render(self, goal: str, context: str, piece: str) -> str:
        env = Environment(loader=BaseLoader())
        template = env.from_string(RESEARCH_PROMPT)
        return template.render(
            goal=goal,
            context=context,
            piece=piece,
            language=self.language,
        )

    def validate_response(self, response: str) -> ResearchResponse | None:
        response = response.strip().replace("```json", "```")

        if response.startswith("```") and response.endswith("```"):
            response = response[3:-3].strip()

        try:
            response = json.loads(response)
        except Exception as _:
            return None

        if "draft" not in response or "action" not in response:
            return None
        else:
            return ResearchResponse(response["draft"], response["action"])

    def execute(self, goal: str, context: str, piece: str) -> ResearchResponse:
        prompt = self.render(goal, context, piece)
        response = self.chat_model.inference(prompt)

        valid_response: Optional[ResearchResponse] = self.validate_response(response)

        while valid_response is None:
            print("Invalid response from the model, trying again...")
            return self.execute(goal, context, piece)

        return valid_response


class Investigation:
    def __init__(self, chat_model: ChatModel, language: str):
        self.logger = Logger()
        self.chat_model = chat_model
        self.language = language

    def render(self, goal: str, context: str) -> str:
        env = Environment(loader=BaseLoader())
        template = env.from_string(INVESTIGATION_PROMPT)
        return template.render(
            goal=goal,
            context=context,
            language=self.language,
        )

    def validate_response(self, response: str) -> str | None:
        response = response.strip().replace("```json", "```")

        if response.startswith("```") and response.endswith("```"):
            response = response[3:-3].strip()

        try:
            response = json.loads(response)
        except Exception as _:
            return None

        if "result" not in response:
            return None
        else:
            return response["result"]

    def execute(self, goal: str, context: str) -> str:
        prompt = self.render(goal, context)
        response = self.chat_model.inference(prompt)

        valid_response: Optional[str] = self.validate_response(response)

        while valid_response is None:
            print("Invalid response from the model, trying again...")
            return self.execute(goal, context)

        return valid_response
