import os
from dataclasses import dataclass
from typing import Optional

import requests
from dotenv import load_dotenv
from huggingface_hub import InferenceClient


@dataclass
class LLMConfig:
    mode: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 512
    base_url: Optional[str] = None
    api_key: Optional[str] = None


class LLMClient:
    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        load_dotenv()

        self.config = config or self._load_config_from_env()

        if self.config.mode not in {"hf", "local"}:
            raise ValueError("LLM mode must be either 'hf' or 'local'.")

        if self.config.mode == "hf":
            if not self.config.api_key:
                raise RuntimeError("HF_TOKEN is missing. Set it in your .env file.")

            self.hf_client = InferenceClient(token=self.config.api_key)
        else:
            if not self.config.base_url:
                raise RuntimeError("LOCAL_LLM_BASE_URL is missing. Set it in your .env file.")

    def _load_config_from_env(self) -> LLMConfig:
        mode = os.getenv("LLM_MODE", "hf").strip().lower()
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "512"))

        if mode == "hf":
            return LLMConfig(
                mode="hf",
                model=os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
                api_key=os.getenv("HF_TOKEN"),
                temperature=temperature,
                max_tokens=max_tokens,
            )

        if mode == "local":
            return LLMConfig(
                mode="local",
                model=os.getenv("LOCAL_LLM_MODEL", "local-model"),
                base_url=os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:8000/v1"),
                api_key=os.getenv("LOCAL_LLM_API_KEY", ""),
                temperature=temperature,
                max_tokens=max_tokens,
            )

        raise ValueError("LLM_MODE must be either 'hf' or 'local'.")

    def generate(self, prompt: str) -> str:
        if self.config.mode == "hf":
            return self._generate_hf(prompt)

        return self._generate_local(prompt)

    def _generate_hf(self, prompt: str) -> str:
        completion = self.hf_client.chat_completion(
            model=self.config.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        return completion.choices[0].message.content.strip()

    def _generate_local(self, prompt: str) -> str:
        assert self.config.base_url is not None

        base_url = self.config.base_url.rstrip("/")
        url = f"{base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
        }

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()

        data = response.json()

        try:
            return data["choices"][0]["message"]["content"].strip()
        except KeyError as exc:
            raise RuntimeError(f"Unexpected local LLM response format: {data}") from exc