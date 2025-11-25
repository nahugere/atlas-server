import configparser
from groq import Groq

config = configparser.ConfigParser()
config.read("config.ini")

config.get('UPSTASH', 'url')


class GroqAgent:

    def __init__(self, context=[]):
        self.client = Groq(api_key=config.read("GROQ", "apikey"))
        self.context = context
    
    def groq_chat(self, text):
        completion = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=self.context,
            temperature=1,
            max_completion_tokens=8192,
            top_p=1,
            reasoning_effort="medium",
            stream=True,
            stop=None,
            tools=[{"type":"browser_search"}]
        )
        return completion.choices[0].message["content"]
    
    def update_context(self, message):
        self.context.append({
            "role": "user",
            "content": message
        })

groq_service = GroqAgent()