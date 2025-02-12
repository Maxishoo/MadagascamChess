import time

from openai import OpenAI
from typing import List, Dict
from abc import abstractmethod, ABC

class ChatClient:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def __str__(self):
        return f'[{self.model}]'

    def __repr__(self):
        return f'[{self.model}]'

    def create_completion(self, messages: List[Dict[str, str]]) -> Dict[str, str]:
        if isinstance(messages, dict):
            messages = [messages]

        content = None
        while content is None:
            time.sleep(1)
            try:
                completion = self.client.chat.completions.create(
                    extra_headers={},
                    extra_body={},
                    model=self.model,
                    messages=messages
                )
                content = completion.choices[0].message.content
            except:
                print('[ERROR] Completion is None')
                continue

        return {
            'role': 'assistant',
            'content': content
        }

    def make_system_prompt(self, system_prompt: str) -> Dict[str, str]:
        return {
            'role': 'system',
            'content': system_prompt
        }
    
    def make_user_prompt(self, user_prompt: str) -> Dict[str, str]:
        return {
            'role': 'user',
            'content': user_prompt
        }