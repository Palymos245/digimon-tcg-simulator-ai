import asyncio
import json
import os
from typing import Any

import requests

from .decision_provider import DecisionProvider


class OpenAIResponsesDecisionProvider(DecisionProvider):
    """Minimal OpenAI Responses API adapter using the repo's existing requests dependency."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.model = os.environ.get("OPENAI_MODEL", "")
        self.base_url = os.environ.get(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        ).rstrip("/")
        self.timeout = float(os.environ.get("OPENAI_TIMEOUT", "30"))
        self.max_output_tokens = int(
            os.environ.get("OPENAI_MAX_OUTPUT_TOKENS", "200")
        )

        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for the LLM bot.")
        if not self.model:
            raise RuntimeError("OPENAI_MODEL is required for the LLM bot.")

    async def choose_action(
        self,
        state_view: dict[str, Any],
        candidates: list[dict[str, Any]],
    ) -> str:
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are the strategic decision-maker for a Digimon TCG bot. "
                                "Choose exactly one candidate action. The candidates are high-level "
                                "routines implemented by a deterministic simulator. Never invent an "
                                "action, card, target, or rule. Prefer a strategically sound action "
                                "based only on the provided legal-information state. Return JSON only."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(
                                {"state": state_view, "candidates": candidates},
                                separators=(",", ":"),
                            ),
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "digimon_action",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string"},
                        },
                        "required": ["action"],
                        "additionalProperties": False,
                    },
                }
            },
            "max_output_tokens": self.max_output_tokens,
        }

        def _request() -> requests.Response:
            return requests.post(
                f"{self.base_url}/responses",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )

        response = await asyncio.to_thread(_request)
        response.raise_for_status()
        data = response.json()

        output_text = data.get("output_text")
        if not output_text:
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") in ("output_text", "text") and content.get("text"):
                        output_text = content["text"]
                        break
                if output_text:
                    break

        if not output_text:
            raise RuntimeError("OpenAI Responses API returned no text output.")

        parsed = json.loads(output_text)
        action = parsed.get("action")
        if not isinstance(action, str) or not action:
            raise RuntimeError("LLM response did not contain a valid action.")
        return action
