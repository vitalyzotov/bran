from app.llm import ChatModel
from app.logger import Logger
from jinja2 import Environment, BaseLoader

PROMPT = open("app/agents/summary/prompt.jinja2", "r").read().strip()


class Summary:
    def __init__(self, chat_model: ChatModel, language: str):
        self.logger = Logger()
        self.chat_model = chat_model
        self.language = language

    def render(self, summary: str, new_lines: str) -> str:
        env = Environment(loader=BaseLoader())
        template = env.from_string(PROMPT)
        return template.render(
            summary=summary,
            new_lines=new_lines,
            language=self.language,
        )

    def validate_response(self, response: str) -> str:
        return response

    def execute(self, summary: str, new_lines: str) -> str:
        prompt = self.render(summary, new_lines)
        response = self.chat_model.inference(prompt)

        valid_response = self.validate_response(response)

        while not valid_response:
            print("Invalid response from the model, trying again...")
            return self.execute(summary, new_lines)

        return valid_response
