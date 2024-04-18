from openai import AzureOpenAI, OpenAI


class ChatModel:
    def __init__(self, model_id: str, is_azure: bool = False):
        self.client = AzureOpenAI() if is_azure else OpenAI()
        self.model_id = model_id

    def inference(self, prompt: str) -> str:
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt.strip(),
                }
            ],
            model=self.model_id,
        )
        response = chat_completion.choices[0].message.content
        return response
