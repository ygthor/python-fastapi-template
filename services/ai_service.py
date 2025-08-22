from fastapi import File, UploadFile, HTTPException
import json
from google import genai
from google.genai import types
from typing import Optional, Dict, List
from core.config import settings
import os
import logging
import re


# Initialize Gemini Client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
client = genai.Client(
    vertexai=True,
    project=settings.GOOGLE_PROJECT_NAME,
    location=settings.GOOGLE_PROJECT_LOCATION,
)

def extract_json_from_response(text: str) -> dict:
    try:
        match = re.search(r'{.*}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print("Error extracting JSON:", e)
    return {}

class AiService:
    # Centralized type mapping
    TYPE_MAP = {
        "string": genai.types.Type.STRING,
        "number": genai.types.Type.NUMBER,
        "date": genai.types.Type.STRING,  # Dates as YYYY-MM-DD strings
        "array_string": genai.types.Type.ARRAY,
        "object": genai.types.Type.OBJECT
    }

    async def _parse_document(self, file: UploadFile, prompt: str, response_schema: genai.types.Schema) -> Optional[Dict]:
        try:
            # Read file bytes
            file_bytes = await file.read()
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part(text=prompt),
                        types.Part(
                            inline_data=types.Blob(
                                mime_type=file.content_type,
                                data=file_bytes
                            )
                        )
                    ]
                )
            ]

            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                response_mime_type="application/json",
                response_schema=response_schema
            )

            response = client.models.generate_content(
                model=settings.GOOGLE_GEMINI_MODEL,
                contents=contents,
                config=config,
            )

            return json.loads(response.text)
        except Exception as e:
            print(f"Error generating content: {e}")
            return None

    async def receipt_parser(self, image: UploadFile) -> Optional[Dict]:
        prompt = "When generating structured data, convert all date-related fields to the format YYYY-MM-DD. If the image does NOT contain a valid receipt or invoice, leave all fields empty."
        schema = genai.types.Schema(
            type=genai.types.Type.OBJECT,
            required=["invoice_date", "total_amount", "invoice_number", "merchant_name"],
            properties={
                "invoice_date": genai.types.Schema(type=self.TYPE_MAP["string"]),
                "total_amount": genai.types.Schema(type=self.TYPE_MAP["number"]),
                "invoice_number": genai.types.Schema(type=self.TYPE_MAP["string"]),
                "merchant_name": genai.types.Schema(type=self.TYPE_MAP["string"]),
            }
        )
        return await self._parse_document(image, prompt, schema)

    async def receipt_parser_1stavenue(self, image: UploadFile) -> Optional[Dict]:
        prompt = "When generating structured data, convert all date-related fields to the format YYYY-MM-DD."
        schema = genai.types.Schema(
            type=genai.types.Type.OBJECT,
            required=["invoice_date", "total_amount", "invoice_number", "merchant_name"],
            properties={
                "invoice_date": genai.types.Schema(type=self.TYPE_MAP["string"]),
                "total_amount": genai.types.Schema(type=self.TYPE_MAP["number"]),
                "invoice_number": genai.types.Schema(type=self.TYPE_MAP["string"]),
                "merchant_name": genai.types.Schema(type=self.TYPE_MAP["string"]),
            }
        )
        return await self._parse_document(image, prompt, schema)
    
    async def vclaim_parser(self, image: UploadFile, custom_fields: Optional[Dict[str, str]] = None) -> Optional[Dict]:
        prompt = "Extract structured data from this claim-related image. Convert all date-related fields to the format YYYY-MM-DD."

        # Sample fallback or default fields if none provided
        custom_fields = custom_fields or {
            "date": "date",
            "invoice_no": "string",
            "total_amount": "string",
        }

        prompt += "\nInclude the following fields:\n" + "\n".join(f"- {k} ({v})" for k, v in custom_fields.items())

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.debug(custom_fields)
        logging.debug(prompt)
        
        schema = self._build_schema_from_custom_fields(custom_fields)

        return await self._parse_document(image, prompt, schema)

    async def resume_parser(self, document: UploadFile, custom_fields: Optional[Dict[str, str]] = None, positions: Optional[List[str]] = None) -> Optional[Dict]:
        prompt = (
            "Extract structured information from this resume/CV document. "
            "Return all fields in JSON. Standard fields include:\n"
            "- name\n- phone\n- email\n- address\n- skills\n- years_of_experience\n"
            "- education\n- work_experience\n- languages"
        )
        
        # Default custom fields
        custom_fields = custom_fields or {
            "current_company": "string",
            "current_position": "string",
            "profile_summary": "string",
            "dob": "date",
            "linkedin": "string",
            "facebook": "string",
            "skill_summary": "string",
            "gender": "string",
            "race": "string",
            "marital_status": "string",
            "country": "string",
            "malaysia_new_ic": "string",
            "malaysia_old_ic": "string",
            "passport_no": "string",
            "certifications": "array_string"
        }

        if custom_fields:
            prompt += "\nAlso include the following custom fields:\n" + "\n".join(f"- {field} ({ftype})" for field, ftype in custom_fields.items())

        # Build schema
        properties = {
            "name": genai.types.Schema(type=self.TYPE_MAP["string"]),
            "phone": genai.types.Schema(type=self.TYPE_MAP["string"]),
            "email": genai.types.Schema(type=self.TYPE_MAP["string"]),
            "address": genai.types.Schema(type=self.TYPE_MAP["string"]),
            "skills": genai.types.Schema(type=self.TYPE_MAP["array_string"], items=genai.types.Schema(type=self.TYPE_MAP["string"])),
            "years_of_experience": genai.types.Schema(type=self.TYPE_MAP["number"]),
            "education": genai.types.Schema(
                type=self.TYPE_MAP["array_string"],
                items=genai.types.Schema(
                    type=self.TYPE_MAP["object"],
                    properties={
                        "college_university": genai.types.Schema(type=self.TYPE_MAP["string"]),
                        "qualification": genai.types.Schema(type=self.TYPE_MAP["string"]),
                        "grade": genai.types.Schema(type=self.TYPE_MAP["string"]),
                        "cgpa": genai.types.Schema(type=self.TYPE_MAP["number"]),  # Optional if applicable
                        "major": genai.types.Schema(type=self.TYPE_MAP["string"]),
                        "completion_year": genai.types.Schema(type=self.TYPE_MAP["string"]),
                        "field_of_study": genai.types.Schema(
                            type=self.TYPE_MAP["array_string"],
                            items=genai.types.Schema(type=self.TYPE_MAP["string"])
                        ),
                    }
                )
            ),
            "work_experience": genai.types.Schema(
                type=self.TYPE_MAP["array_string"],
                items=genai.types.Schema(
                    type=self.TYPE_MAP["object"],
                    properties={
                        "company": genai.types.Schema(type=self.TYPE_MAP["string"]),
                        "role": genai.types.Schema(type=self.TYPE_MAP["string"]),
                        "start_date": genai.types.Schema(type=self.TYPE_MAP["string"]),
                        "end_date": genai.types.Schema(type=self.TYPE_MAP["string"]),
                        "description": genai.types.Schema(type=self.TYPE_MAP["string"]),
                    }
                )
            ),
            "languages": genai.types.Schema(
                type=self.TYPE_MAP["array_string"],
                items=genai.types.Schema(
                    type=self.TYPE_MAP["object"],
                    properties={
                        "language": genai.types.Schema(type=self.TYPE_MAP["string"]),
                        "spoken": genai.types.Schema(type=self.TYPE_MAP["number"]),
                        "written": genai.types.Schema(type=self.TYPE_MAP["number"]),
                    }
                )
            )
        }

        # Add custom fields to schema
        for field, ftype in custom_fields.items():
            field_type = self.TYPE_MAP.get(ftype.lower(), self.TYPE_MAP["string"])
            if field_type == genai.types.Type.ARRAY:
                properties[field] = genai.types.Schema(type=field_type, items=genai.types.Schema(type=self.TYPE_MAP["string"]))
            else:
                properties[field] = genai.types.Schema(type=field_type)

        schema = genai.types.Schema(type=genai.types.Type.OBJECT, properties=properties)
        resume_data = await self._parse_document(document, prompt, schema)

        # If positions provided, evaluate them
        matched_positions = []
        if positions and resume_data:
            position_prompt = (
                "Based on the candidate's resume data below, determine which of the following job positions "
                "they are best suited for. For each match, explain briefly why they are suitable.\n\n"
                f"Candidate resume:\n{json.dumps(resume_data, indent=2)}\n\n"
                f"Available positions:\n{json.dumps(positions)}\n\n"
                "Return the result in this JSON format:\n"
                "{ matched_positions: [ { position: string, reason: string } ] }"
            )

            response = client.models.generate_content(
                model=settings.GOOGLE_GEMINI_MODEL,
                contents=[types.Content(role="user", parts=[types.Part(text=position_prompt)])],
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    top_k=40,
                    top_p=0.95,
                    max_output_tokens=2048,
                    response_mime_type="application/json"
                )
            )
            matched_json = extract_json_from_response(response.text)  # Your utility to safely parse the response
            resume_data["matched_positions"] = matched_json.get("matched_positions", [])
        
        return resume_data

    def _build_schema_from_custom_fields(self, custom_fields: Dict[str, str]) -> genai.types.Schema:
        properties = {}
        for field, ftype in custom_fields.items():
            resolved_type = self.TYPE_MAP.get(ftype.lower(), self.TYPE_MAP["string"])
            if resolved_type == genai.types.Type.ARRAY:
                properties[field] = genai.types.Schema(type=resolved_type, items=genai.types.Schema(type=self.TYPE_MAP["string"]))
            else:
                properties[field] = genai.types.Schema(type=resolved_type)
        
        return genai.types.Schema(type=genai.types.Type.OBJECT, properties=properties)

    async def chat(self, prompt: str) -> str:
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                )
            ]

            config = types.GenerateContentConfig(
                temperature=0.5,
                top_k=40,
                top_p=0.95,
                max_output_tokens=2048,
            )

            response = client.models.generate_content(
                model=settings.GOOGLE_GEMINI_MODEL,
                contents=contents,
                config=config,
            )

            candidates = getattr(response, "candidates", [])
            if not candidates or not candidates[0].content or not candidates[0].content.parts:
                raise Exception("Empty response from Gemini")

            return candidates[0].content.parts[0].text.strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI summary error: {str(e)}")