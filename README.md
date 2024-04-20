# Bran, an AI-powered Software Analyst

## About

Bran is an AI-powered software analyst that was inspired by Devika. It uses planning to break down its tasks 
and incremental proofreading to help users achieve their goals in the domain of system analysis.

The project in the prototype stage to see if this approach is feasible.

## Getting Started

### Requirements
  
- Python 3.11
- Install uv - Python Package manager [download](https://github.com/astral-sh/uv)
- Install docker and docker compose plugin

### Installation

Please follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/vitalyzotov/bran.git
   ```
2. Navigate to the project directory:
   ```bash
   cd bran
   ```
3. Create a virtual environment and install the required dependencies (you can use any virtual environment manager):
   ```bash
   uv venv
   
   # On macOS and Linux.
   source .venv/bin/activate

   # On Windows.
   .venv\Scripts\activate

   uv pip install -r requirements.txt
   ```
4. Start [Phoenix](https://docs.arize.com/phoenix) to collect LLM tracing:
   ```bash
   docker compose up -d
   ```
5. Configure your environment variables:
   
   For Azure OpenAI Service:
   ```bash
   AZURE_OPENAI_API_KEY="<your key>"
   OPENAI_API_VERSION="<your api version, e.g. 2023-05-15>"
   AZURE_OPENAI_ENDPOINT="<your endpoint, something like https://???.openai.azure.com>"
   CHAT_MODEL_AZURE=True
   CHAT_MODEL_ID="<your model id, like gpt-35-turbo-0613>"
   DATA_PATH="<path to your text file for analysis>"
   ```
   For OpenAI:
   ```bash
   OPENAI_API_KEY="<your key>"
   CHAT_MODEL_ID="<your model id, like gpt-3.5-turbo-0125>"
   DATA_PATH="<path to your text file for analysis>"
   ```
6. Start Bran:
   ```bash
   python ask_bran.py
   ```
   Use the program arguments `--lang` to specify the language and `--prompt` to define your goal. 
   Bran will ask you for the goal if you don't specify it.