from abc import ABC
import json
import time

from app.external.openrouter_client import OpenRouterClient
from app.utils.prompt_loader import load_prompt
from app.utils.json_parser import JSONParser
from app.utils.output_validator import OutputValidator


class BaseAgent(ABC):
    """Base class for AI agents using the OpenRouter client."""

    def __init__(self, prompt_file: str, required_fields: list | None = None):
        self.client = OpenRouterClient()
        self.prompt = load_prompt(prompt_file)
        self.required_fields = required_fields or []

    def execute(self, input_data: dict, temperature: float = 0.3):
        start_time = time.perf_counter()

        user_prompt = json.dumps(
            input_data,
            indent=2,
            ensure_ascii=False,
        )

        # One LLM request per agent execution. JSON validation is local and
        # does not trigger another model request; this prevents accidental
        # request multiplication when an API quota is tight.
        response = self.client.generate(
            system_prompt=self.prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            retries=1,
        )

        parsed = JSONParser.parse(response)
        OutputValidator.validate(parsed, self.required_fields)

        execution_time = round(time.perf_counter() - start_time, 3)

        print(f"✅ {self.__class__.__name__} completed in {execution_time}s")

        return {
            "success": True,
            "agent": self.__class__.__name__,
            "execution_time": execution_time,
            "data": parsed,
        }

    # Compatibility for the existing TestAgent implementation.
    def run(self, input_data: dict):
        return self.execute(input_data)
