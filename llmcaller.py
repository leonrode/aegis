import os
from google import genai
from google.genai.types import Part

class LLMCaller:
    """ Responsible for calling an LLM and returning the response """
    def __init__(self, tools_config=None):
        self.llm_client = None
        self.tools_config = tools_config
        self.init_llm_client()

    
    def init_llm_client(self):
        self.llm_client = genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"], location=os.environ["GOOGLE_CLOUD_LOCATION"])

    def call_llm(self, prompt, conversation_history=None):
        if conversation_history:
            response = self.llm_client.models.generate_content(
                model="gemini-2.0-flash-lite-001",
                contents = conversation_history + [Part.from_text(text=prompt)],
                config=self.tools_config
            )
        else:
            response = self.llm_client.models.generate_content(
                model="gemini-2.0-flash-lite-001",
                contents = [Part.from_text(text=prompt)],
                config=self.tools_config
            )

        return response
