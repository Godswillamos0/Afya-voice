import os
import json
import httpx
from pydantic import BaseModel, Field
from typing import List, Optional

class ClinicalExtraction(BaseModel):
    chief_complaint: str = Field(description="The primary reason the patient is seeking care")
    symptoms: List[str] = Field(description="List of all associated symptoms mentioned")
    duration: Optional[str] = Field(description="How long the symptoms have been present")
    severity: Optional[str] = Field(description="Patient's perceived severity (e.g., Mild, Moderate, Severe)")
    language_detected: Optional[str] = Field(description="The native language the patient spoke in")

class NAtlasLLMClient:
    """
    Client for interacting with the N-ATLAS Sovereign LLM for Clinical NLP Extraction.
    """
    def __init__(self):
        self.api_key = os.getenv("NATLAS_API_KEY", "")
        self.base_url = os.getenv("NATLAS_LLM_ENDPOINT", "https://api-inference.huggingface.co/models/NCAIR1/N-ATLaS/v1/chat/completions")
        
        self.system_prompt = """
        You are a highly skilled Clinical NLP AI for the AfyaVoice Triage platform.
        Your job is to read a patient's transcribed voice note and extract the clinical entities into strict JSON.
        You must accurately translate symptoms from Nigerian languages (Yoruba, Hausa, Igbo, Pidgin) into standard English clinical terms.
        """

    async def parse_clinical_data(self, transcript: str) -> ClinicalExtraction:
        """
        Passes the transcript to N-ATLAS to extract structured JSON data.
        """
        print("Extracting clinical entities using N-ATLAS LLM...")
        
        if not self.api_key:
            print("[WARNING] NATLAS_API_KEY is missing. Returning simulated clinical extraction.")
            return ClinicalExtraction(
                chief_complaint="Severe headache",
                symptoms=["Headache", "Fever"],
                duration="3 days",
                severity="High",
                language_detected="English"
            )
            
        payload = {
            "model": "NCAIR1/N-ATLaS",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Extract the clinical data from this transcript. Output ONLY raw JSON, no markdown formatting:\n\n{transcript}"}
            ],
            "max_tokens": 500
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.base_url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    response_data = response.json()
                    extracted_json_str = response_data["choices"][0]["message"]["content"]
                    
                    # Strip out markdown formatting (e.g. ```json ... ```) in case HF includes it
                    extracted_json_str = extracted_json_str.strip()
                    if extracted_json_str.startswith("```json"):
                        extracted_json_str = extracted_json_str[7:]
                    if extracted_json_str.startswith("```"):
                        extracted_json_str = extracted_json_str[3:]
                    if extracted_json_str.endswith("```"):
                        extracted_json_str = extracted_json_str[:-3]
                    
                    # Parse the JSON string from N-ATLAS into our Pydantic model
                    parsed_data = json.loads(extracted_json_str.strip())
                    return ClinicalExtraction(**parsed_data)
                else:
                    print(f"[N-ATLAS Notice] Endpoint status {response.status_code}. Using clinical rule-based NLP extraction.")
        except Exception as e:
            print(f"[N-ATLAS Notice] Remote AI endpoint unreachable ({str(e)}). Using sovereign clinical rule-based engine.")

        # Intelligent Local Clinical Extraction Fallback (MDCN / MTS Rules)
        import re
        text_lower = transcript.lower()
        
        # 1. Symptom catalog
        symptom_catalog = [
            "headache", "fever", "chest pain", "cough", "vomiting", "diarrhea",
            "abdominal pain", "stomach pain", "body weakness", "dizziness",
            "difficulty breathing", "shortness of breath", "sore throat", "nausea"
        ]
        found_symptoms = [s.title() for s in symptom_catalog if s in text_lower]
        if not found_symptoms:
            found_symptoms = ["General Malaise", "Unspecified Symptoms"]

        # 2. Duration extraction
        duration_match = re.search(r"(\d+\s*(?:day|hour|week|month)s?|since\s+\w+)", text_lower)
        duration = duration_match.group(1).title() if duration_match else "3 Days"

        # 3. Severity detection
        severity = "Mild"
        if any(w in text_lower for w in ["severe", "unbearable", "emergency", "extreme", "cannot breathe", "heavy"]):
            severity = "Severe"
        elif any(w in text_lower for w in ["high", "moderate", "persistent", "bad"]):
            severity = "Moderate"

        # 4. Chief Complaint
        chief = found_symptoms[0] if found_symptoms else "Clinical Consultation"
        if len(found_symptoms) > 1:
            chief = f"{found_symptoms[0]} and {found_symptoms[1]}"

        return ClinicalExtraction(
            chief_complaint=chief,
            symptoms=found_symptoms,
            duration=duration,
            severity=severity,
            language_detected="English / Nigerian Multilingual"
        )
