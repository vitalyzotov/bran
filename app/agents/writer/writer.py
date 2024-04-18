import json
from dataclasses import dataclass
from typing import Optional

from app.llm import ChatModel
from app.logger import Logger
from jinja2 import Environment, BaseLoader

STRUCTURE_PROMPT = open("app/agents/writer/structure.prompt.jinja2", "r").read().strip()
SECTION_PROMPT = open("app/agents/writer/section.prompt.jinja2", "r").read().strip()
KNOWLEDGE_PROMPT = open("app/agents/writer/knowledge.prompt.jinja2", "r").read().strip()


@dataclass(frozen=True)
class StructureResponse:
    title: str
    sections: list[str]


class Structure:
    def __init__(self, chat_model: ChatModel, language: str):
        self.logger = Logger()
        self.chat_model = chat_model
        self.language = language

    def render(self, objective: str, plan: str, step: str) -> str:
        env = Environment(loader=BaseLoader())
        template = env.from_string(STRUCTURE_PROMPT)
        return template.render(
            objective=objective,
            plan=plan,
            step=step,
            language=self.language,
        )

    def validate_response(self, response: str) -> StructureResponse | None:
        response = response.strip().replace("```json", "```")

        if response.startswith("```") and response.endswith("```"):
            response = response[3:-3].strip()

        try:
            response = json.loads(response)
        except Exception as _:
            return None

        if "title" not in response or "sections" not in response:
            return None
        else:
            return StructureResponse(response["title"], response["sections"])

    def execute(self, objective: str, plan: str, step: str) -> StructureResponse:
        prompt = self.render(objective, plan, step)
        response = self.chat_model.inference(prompt)

        valid_response: Optional[StructureResponse] = self.validate_response(response)

        while valid_response is None:
            print("Invalid response from the model, trying again...")
            return self.execute(objective, plan, step)

        return valid_response


@dataclass(frozen=True)
class WriterKnowledgeResponse:
    need_more_data: list[str]


class WriterKnowledge:
    def __init__(self, chat_model: ChatModel, language: str):
        self.logger = Logger()
        self.chat_model = chat_model
        self.language = language

    def render(self,
               objective: str,
               plan: str,
               step: str,
               knowledge_keys: list[str],
               section: str) -> str:
        env = Environment(loader=BaseLoader())
        template = env.from_string(KNOWLEDGE_PROMPT)
        return template.render(
            objective=objective,
            plan=plan,
            step=step,
            knowledge_keys=knowledge_keys,
            section=section,
            language=self.language,
        )

    def validate_response(self, response: str) -> WriterKnowledgeResponse | None:
        response = response.strip().replace("```json", "```")

        if response.startswith("```") and response.endswith("```"):
            response = response[3:-3].strip()

        try:
            response = json.loads(response)
        except Exception as _:
            return None

        if "need_more_data" not in response:
            return None
        else:
            return WriterKnowledgeResponse(response["need_more_data"])

    def execute(self, objective: str, plan: str, step: str, knowledge: dict[str, str],
                section: str) -> WriterKnowledgeResponse:
        def initial_step():
            return self.chat_model.inference(self.render(objective, plan, step, list(knowledge.keys()), section))

        def validate_step(response):
            return self.validate_response(response)

        while True:
            response = initial_step()
            valid_response = validate_step(response)

            if valid_response is None:
                print("Invalid response from the model, trying initial step again...")
            return valid_response


class SectionWriter:
    def __init__(self, chat_model: ChatModel, language: str):
        self.logger = Logger()
        self.chat_model = chat_model
        self.language = language

    def render(self,
               objective: str,
               plan: str,
               step: str,
               knowledge: list[str],
               section: str) -> str:
        env = Environment(loader=BaseLoader())
        template = env.from_string(SECTION_PROMPT)
        return template.render(
            objective=objective,
            plan=plan,
            step=step,
            knowledge=knowledge,
            section=section,
            language=self.language,
        )

    def validate_response(self, response: str) -> str:
        response = response.strip().replace("```md", "```")

        if response.startswith("```") and response.endswith("```"):
            response = response[3:-3].strip()

        return response

    def execute(self,
                objective: str,
                plan: str,
                step: str,
                knowledge: list[str],
                section: str) -> str:
        def initial_step():
            return self.chat_model.inference(self.render(objective, plan, step, knowledge, section))

        def validate_step(response):
            return self.validate_response(response)

        while True:
            response = initial_step()
            initial_response = validate_step(response)

            if not initial_response:
                print("Invalid response from the model, trying again...")
            return initial_response
