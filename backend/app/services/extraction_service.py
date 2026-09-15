import json
import os

from dotenv import load_dotenv
from groq import Groq

from app.schemas.extraction import PrescriptionExtraction


load_dotenv()


class ExtractionService:

    def __init__(self):
        # Load API key from .env
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured"
            )

        # Load model from .env
        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        )

        self.client = Groq(
            api_key=api_key
        )

    def extract(
        self,
        ocr_text: str
    ) -> PrescriptionExtraction:

        system_prompt = """
You are a healthcare document extraction assistant.

Your task is to extract structured information
from OCR text.

STRICT SAFETY RULES:

1. Use ONLY information explicitly present
   in the provided OCR text.

2. NEVER guess or infer missing medical
   information.

3. NEVER use outside medical knowledge to
   fill missing fields.

4. If a field is not supported by the OCR text,
   return null.

5. Preserve medicine names exactly as supported
   by the OCR text.

6. Preserve strengths exactly as supported
   by the OCR text.

7. Do not create a strength from general knowledge.

8. Do not create dosage instructions that are
   not present in the source.

9. Do not create frequency information that
   is not present in the source.

10. Return ONLY JSON.

11. Follow the requested JSON structure.
"""

        user_prompt = f"""
Extract structured information from this OCR text.

OCR TEXT:
----------------
{ocr_text}
----------------

Return exactly this JSON structure:

{{
    "medicine_name": null,
    "active_ingredients": [],
    "strength": {{
        "value": null
    }},
    "dosage_form": null,
    "quantity": null,
    "instructions": null,
    "frequency": null
}}

Rules:

- medicine_name:
  Extract only if explicitly supported.

- active_ingredients:
  Include only ingredients explicitly
  supported by the OCR text.

- strength:
  Include only explicitly detected strength.
  If unsupported, return null.

- dosage_form:
  Examples include tablet, capsule, syrup,
  injection, etc., but only if supported
  by the OCR text.

- quantity:
  Extract only if explicitly supported.

- instructions:
  Extract only if explicitly present.

- frequency:
  Extract only if explicitly present.

Missing information MUST remain null.

Do not guess.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={
                "type": "json_object"
            },
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "AI returned an empty response"
            )

        # Convert AI JSON string into Python object
        try:
            data = json.loads(content)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "AI returned invalid JSON"
            ) from exc

        # Final Pydantic validation
        try:
            result = PrescriptionExtraction.model_validate(
                data
            )

        except Exception as exc:
            raise ValueError(
                f"AI response failed schema validation: {exc}"
            ) from exc

        return result