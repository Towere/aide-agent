from typing import List, Dict, Any, Optional
from core.config import settings
import json
import logging

logger = logging.getLogger(__name__)

_llm_client_instance = None

class LLMClient:
    def __init__(self):
        self._client = None
        self._model = settings.doubao_model

    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            # Create OpenAI client without proxies parameter
            self._client = OpenAI(
                api_key=settings.ark_api_key,
                base_url=settings.ark_base_url
            )
        return self._client

    @property
    def model(self):
        return self._model

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        try:
            logger.info(f"调用LLM模型: {self.model}")
            # Remove any proxies from kwargs if present
            kwargs.pop('proxies', None)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}", exc_info=True)
            raise Exception(f"LLM调用失败: {str(e)}")

    def chat_with_system_prompt(
        self,
        user_prompt: str,
        system_prompt: str = "你是一个有用的助手。",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.chat(messages, temperature, max_tokens)

    def extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        except Exception:
            return None

def get_llm_client():
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance

llm_client = None
