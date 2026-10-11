
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

        # Compact JSON avoids spending prompt tokens on indentation and whitespace.
        user_prompt = json.dumps(
            input_data,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        print(f"AI system prompt length: {len(self.prompt)} characters")
        print(f"AI user prompt length: {len(user_prompt)} characters")
        print(
            "Combined prompt length: "
            f"{len(self.prompt) + len(user_prompt)} characters"
        )

        response = self.client.generate(
            system_prompt=self.prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            retries=1,
        )

        parsed = None
        last_error = None

        # First attempt parses the original response.
        # A second LLM request is made only if parsing or validation fails.
        for attempt in range(2):
            try:
                if attempt == 1:
                    print(
                        "Invalid JSON/output detected. "
                        "Requesting one corrected response..."
                    )

                    correction_prompt = (
                        "Your previous response was invalid or incomplete. "
                        "Return one corrected, complete JSON object only. "
                        "Do not use Markdown, code fences, or text outside JSON. "
                        "Use double quotes for every key and string value. "
                        "Check every comma, quote, bracket, and brace. "
                        "Include every required field, but keep all descriptions "
                        "and list items concise so the entire JSON fits in the "
                        "available output-token limit. Never stop mid-object."
                    )

                    response = self.client.generate(
                        system_prompt=(
                            self.prompt
                            + "\n\nIMPORTANT JSON OUTPUT RULES:\n"
                            + correction_prompt
                        ),
                        user_prompt=(
                            "Original input:\n"
                            + user_prompt
                            + "\n\nPrevious invalid response:\n"
                            + response
                            + "\n\nParser/validation error: "
                            + str(last_error or "Invalid JSON")
                            + "\n\nCorrect the response and return valid JSON only. "
                            + "Keep it concise and complete."
                        ),
                        temperature=0.1,
                        retries=1,
                    )

                if isinstance(response, str):
                    print(f"AI response length: {len(response)} characters")
                    if response and not response.rstrip().endswith(("}", "]")):
                        print("Warning: AI response may be truncated (JSON closing character missing).")
                parsed = JSONParser.parse(response)
                OutputValidator.validate(parsed, self.required_fields)
                break

            except (ValueError, json.JSONDecodeError) as exc:
                last_error = exc

                if attempt == 1:
                    raise ValueError(
                        f"{self.__class__.__name__} returned invalid JSON "
                        f"or failed output validation after one correction "
                        f"attempt: {exc}"
                    ) from exc

        execution_time = round(time.perf_counter() - start_time, 3)

        print(
            f"✅ {self.__class__.__name__} completed "
            f"in {execution_time}s"
        )

        return {
            "success": True,
            "agent": self.__class__.__name__,
            "execution_time": execution_time,
            "data": parsed,
        }

    # Compatibility for the existing TestAgent implementation.
    def run(self, input_data: dict):
        return self.execute(input_data)
