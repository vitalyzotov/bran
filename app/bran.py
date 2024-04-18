import json
import os

from app.agents.action import Action
from app.agents.action.action import ActionResponse
from app.agents.extract import GiveMeList
from app.agents.investigate import Research, Investigation, ResearchResponse
from app.agents.planner import Planner
from app.agents.summary import Summary
from app.agents.writer import Structure
from app.agents.writer.writer import SectionWriter, WriterKnowledge, WriterKnowledgeResponse
from app.llm import ChatModel
from app.logger import Logger
from phoenix.trace.openai import OpenAIInstrumentor
from spacy.lang.en import English
from spacy.lang.ru import Russian

Logger.dateFmt = "---\\n%y.%m.%d %H:%M:%S"
logger = Logger()

# Initialize OpenAI auto-instrumentation
OpenAIInstrumentor().instrument()


class Bran:
    def __init__(self, language: str = 'Russian'):
        self.language = language
        self.chat_model = ChatModel(model_id=os.environ["CHAT_MODEL_ID"],
                                    is_azure=os.getenv("CHAT_MODEL_AZURE", 'False').lower() in ('true', '1', 't'))
        self.give_me_list = GiveMeList(self.chat_model, language=self.language)
        self.structure_writer = Structure(self.chat_model, language=self.language)
        self.section_writer = SectionWriter(self.chat_model, language=self.language)
        self.writer_knowledge = WriterKnowledge(self.chat_model, language=self.language)
        self.planner = Planner(self.chat_model, language=self.language)
        self.action = Action(self.chat_model)
        self.research = Research(self.chat_model, language=self.language)
        self.summarizer = Summary(self.chat_model, language=self.language)
        self.investigation = Investigation(self.chat_model, language=self.language)
        self.documentation = list()
        self.knowledge = dict()

    def _create_nlp_object(self):
        if self.language == 'Russian':
            return Russian()
        elif self.language == 'English':
            return English()
        # add more languages as needed
        else:
            raise ValueError(f'Unsupported language: {self.language}')

    @property
    def documentation(self) -> list[str]:
        if len(self._documentation) == 0:
            # load text file from data_path
            data_path = os.environ["DATA_PATH"]
            logger.info(f"Loading data from {data_path}")
            with open(data_path, "r", encoding="utf-8") as f:
                text = f.read()

            # split into sentences
            nlp_simple = self._create_nlp_object()
            nlp_simple.add_pipe('sentencizer')
            doc = nlp_simple(text)
            sentences = [str(sent).strip() for sent in doc.sents]

            # make groups of sentences
            group_size = 20
            self._documentation = ["\\n".join(sentences[i: i + group_size]) for i in
                                   range(0, len(sentences), group_size)]
        return self._documentation

    @documentation.setter
    def documentation(self, value: list[str]):
        self._documentation = value

    def prepare_plan(self, objective: str) -> (str, list[str]):
        plan = self.planner.execute(objective)
        plan_items: list[str] = self.give_me_list.execute(plan)
        return plan, plan_items

    def what_should_i_do(self, plan: str, goal: str) -> ActionResponse:
        return self.action.execute(plan, goal)

    def investigate(self, goal):
        context: str = ""
        notes: list[str] = []
        sentences_iterator = iter(self.documentation)
        for sentence in sentences_iterator:
            piece = sentence
            while True:
                outcome: ResearchResponse = self.research.execute(goal, context, piece)
                if outcome.action == "more":
                    try:
                        piece = piece + "\n" + next(sentences_iterator)
                    except StopIteration:
                        pass
                else:
                    break
            context = self.summarizer.execute(context, piece)
            notes.append(outcome.draft)

        text_of_notes = '\n'.join(notes)
        logger.debug(f"Notes: {text_of_notes}")

        investigation_result: str = self.investigation.execute(goal, text_of_notes)
        return investigation_result

    def write_document_structure(self, objective: str, plan: str, step: str):
        return self.structure_writer.execute(objective=objective,
                                             plan=plan,
                                             step=step)

    def write_document_section(self,
                               objective: str,
                               plan: str,
                               step: str,
                               required_knowledge: list[str],
                               section: str) -> str:
        knowledge = [self.knowledge[key] for key in required_knowledge]
        return self.section_writer.execute(objective=objective,
                                           plan=plan,
                                           step=step,
                                           section=section,
                                           knowledge=knowledge)

    def what_should_i_know(self, objective: str, plan: str, step: str, section: str) -> WriterKnowledgeResponse:
        return self.writer_knowledge.execute(objective, plan, step, self.knowledge, section)

    def dump_knowledge(self):
        knowledge_json = json.dumps(self.knowledge, indent=4, ensure_ascii=False)
        logger.debug(f"Resulting knowledge: {knowledge_json}")

    def execute(self, objective: str):
        logger.info("Starting...")

        plan, plan_items = self.prepare_plan(objective=objective)
        logger.info(plan)

        for goal in plan_items:
            logger.info(f"I'm thinking about goal `{goal}`")
            item_action = self.what_should_i_do(plan=plan, goal=goal)
            logger.info(f"My thought is: `{item_action.response}`")
            logger.info(f"I've decided to perform action `{item_action.action}`")

            if item_action.action == 'investigate':
                self.knowledge[goal] = self.investigate(goal)
            elif item_action.action == 'feature' or item_action.action == 'report':
                doc_structure = self.write_document_structure(objective=objective, plan=plan, step=goal)
                logger.info(f"I will generate document `{doc_structure.title}` with sections: "
                            f"{', '.join(doc_structure.sections)}")

                doc_filename = f"{doc_structure.title}.md"
                # delete file if exists
                if os.path.isfile(doc_filename):
                    logger.warning(f"File `{doc_filename}` already exists. I will delete it.")
                    os.remove(doc_filename)

                # write file
                for section in doc_structure.sections:
                    logger.info(f"I'm thinking about section `{section}`")
                    i_want_to_know = self.what_should_i_know(objective=objective,
                                                             plan=plan,
                                                             step=goal,
                                                             section=section).need_more_data
                    logger.info(
                        f"I'm generating content for the section using the results of the steps: {', '.join(i_want_to_know)}")
                    doc_section = self.write_document_section(objective=objective,
                                                              plan=plan,
                                                              step=goal,
                                                              required_knowledge=i_want_to_know,
                                                              section=section)

                    logger.info(f"I've finished writing this section and I'm adding it to the document.")
                    with open(doc_filename, "a", encoding="utf-8") as doc_file:
                        doc_file.write('\n\n')
                        doc_file.write(doc_section)

        self.dump_knowledge()
