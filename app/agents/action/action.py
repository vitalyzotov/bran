import json
from dataclasses import dataclass
from typing import Optional

from app.llm import ChatModel
from app.logger import Logger
from jinja2 import Environment, BaseLoader

PROMPT = open("app/agents/action/prompt.jinja2", "r").read().strip()


@dataclass(frozen=True)
class ActionResponse:
    response: str
    action: str


class Action:
    def __init__(self, chat_model: ChatModel):
        self.logger = Logger()
        self.chat_model = chat_model

    def render(self, step_by_step_plan: str, current_item: str) -> str:
        env = Environment(loader=BaseLoader())
        template = env.from_string(PROMPT)
        return template.render(
            step_by_step_plan=step_by_step_plan,
            current_item=current_item,
        )

    def validate_response(self, response: str) -> ActionResponse | None:
        response = response.strip().replace("```json", "```")

        if response.startswith("```") and response.endswith("```"):
            response = response[3:-3].strip()

        try:
            response = json.loads(response)
        except Exception as _:
            return None

        if "response" not in response or "action" not in response:
            return None
        else:
            return ActionResponse(response["response"], response["action"])

    def execute(self, step_by_step_plan: str, current_item: str) -> ActionResponse:
        prompt = self.render(step_by_step_plan, current_item)
        response = self.chat_model.inference(prompt)

        valid_response: Optional[ActionResponse] = self.validate_response(response)

        while valid_response is None:
            print("Invalid response from the model, trying again...")
            return self.execute(step_by_step_plan, current_item)

        return valid_response
