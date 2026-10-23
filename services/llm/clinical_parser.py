import os
import re
import json
import httpx
from pydantic import BaseModel, Field
from typing import List, Optional
from services.rag.retriever import MaternalRAGRetriever

class ClinicalExtraction(BaseModel):
    chief_complaint: str = Field(description="The primary reason the mother/patient is seeking care")
    symptoms: List[str] = Field(description="List of all associated symptoms mentioned")
    duration: Optional[str] = Field(default="Not specified", description="How long the symptoms have been present")
    severity: Optional[str] = Field(default="Moderate", description="Patient's perceived severity (e.g., Mild, Moderate, Severe)")
    language_detected: Optional[str] = Field(default="English / Nigerian Multilingual", description="The native language the patient spoke in")
    gestational_stage: Optional[str] = Field(default="Unspecified", description="Gestational stage (e.g. 1st Trimester, 2nd Trimester, 3rd Trimester, Postnatal)")
    is_pregnant: bool = Field(default=True, description="Whether the consultation pertains to pregnancy or postpartum")
    danger_signs: List[str] = Field(default_factory=list, description="Obstetric danger signs identified")
    guideline_context: Optional[str] = Field(default="", description="Relevant WHO and Nigerian maternal clinical guidelines retrieved via RAG")

class NAtlasLLMClient:
    """
    Client for interacting with N-ATLAS Sovereign LLM and Maternal RAG Knowledge Base.
    """
    def __init__(self):
        self.api_key = os.getenv("NATLAS_API_KEY", "")
        self.base_url = os.getenv("NATLAS_LLM_ENDPOINT", "https://api-inference.huggingface.co/models/NCAIR1/N-ATLaS/v1/chat/completions")
        self.retriever = MaternalRAGRetriever()
        
        self.system_prompt = """
        You are AfyaMama, a specialized Maternal & Antenatal Healthcare Clinical AI for Nigeria.
        Your expertise is in WHO Antenatal Care Guidelines and the Nigerian Federal Ministry of Health Maternal Protocols.
        Your job is to read a pregnant or postpartum woman's symptoms (spoken in Yoruba, Hausa, Igbo, Nigerian Pidgin, or English),
        cross-reference the retrieved WHO/Nigeria clinical guidelines, and output strict clinical JSON.
        You must detect any life-threatening obstetric danger signs (e.g. Antepartum Haemorrhage, Pre-Eclampsia, Eclampsia, Sepsis, Reduced Fetal Movements).
        """

    async def parse_clinical_data(self, transcript: str, gestational_stage: Optional[str] = None) -> ClinicalExtraction:
        """
        Passes the transcript and retrieved WHO/Nigeria guideline context to the LLM or local clinical engine.
        """
        print("Extracting maternal clinical entities using N-ATLAS LLM & Maternal RAG...")
        
        # 1. Retrieve evidence-based WHO & Nigerian Health Guidelines via RAG
        retrieved_chunks = self.retriever.retrieve(transcript, top_k=2, gestational_stage=gestational_stage)
        guideline_context = self.retriever.format_guideline_context(retrieved_chunks)

        # 2. If API Key is present, attempt remote N-ATLaS LLM extraction
        if self.api_key:
            prompt_content = (
                f"PATIENT TRANSCRIPT:\n{transcript}\n\n"
                f"GESTATIONAL STAGE:\n{gestational_stage or 'Not specified'}\n\n"
                f"AUTHORITATIVE GUIDELINE EVIDENCE (WHO & NIGERIA FMOH):\n{guideline_context}\n\n"
                f"Extract raw JSON adhering to this schema without markdown code blocks:\n"
                f'{{"chief_complaint": "...", "symptoms": ["..."], "duration": "...", "severity": "Mild|Moderate|Severe", "language_detected": "...", "gestational_stage": "...", "is_pregnant": true, "danger_signs": ["..."]}}'
            )

            payload = {
                "model": "NCAIR1/N-ATLaS",
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt_content}
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
                        extracted_json_str = response_data["choices"][0]["message"]["content"].strip()
                        
                        if extracted_json_str.startswith("```json"):
                            extracted_json_str = extracted_json_str[7:]
                        if extracted_json_str.startswith("```"):
                            extracted_json_str = extracted_json_str[3:]
                        if extracted_json_str.endswith("```"):
                            extracted_json_str = extracted_json_str[:-3]
                        
                        parsed_data = json.loads(extracted_json_str.strip())
                        parsed_data["guideline_context"] = guideline_context
                        return ClinicalExtraction(**parsed_data)
                    else:
                        print(f"[N-ATLAS Notice] Endpoint status {response.status_code}. Using maternal rule-based clinical engine.")
            except Exception as e:
                print(f"[N-ATLAS Notice] Remote AI endpoint unreachable ({str(e)}). Using maternal rule-based clinical engine.")

        # 3. Intelligent Local Maternal Clinical Rule Engine (WHO / FMOH Nigeria Protocols)
        text_lower = transcript.lower()

        # Detect Gestational Stage
        stage = gestational_stage or "Unspecified"
        if "first trimester" in text_lower or "1st trimester" in text_lower or "2 months" in text_lower or "3 months" in text_lower:
            stage = "First Trimester"
        elif "second trimester" in text_lower or "2nd trimester" in text_lower or "4 months" in text_lower or "5 months" in text_lower or "6 months" in text_lower:
            stage = "Second Trimester"
        elif "third trimester" in text_lower or "3rd trimester" in text_lower or "7 months" in text_lower or "8 months" in text_lower or "9 months" in text_lower or "labor" in text_lower:
            stage = "Third Trimester"
        elif "delivered" in text_lower or "gave birth" in text_lower or "postpartum" in text_lower or "baby born" in text_lower:
            stage = "Postnatal / New Mother"

        # Detect Obstetric Danger Signs
        danger_signs = []
        if any(w in text_lower for w in ["bleed", "blood", "eje", "spotting", "zubar jini", "obara"]):
            danger_signs.append("Vaginal Bleeding / Antepartum Haemorrhage")
        if any(w in text_lower for w in ["convulsion", "seizure", "fitting", "warapa", "farfadiya"]) or (("headache" in text_lower or "ori fifo" in text_lower or "ciwon kai" in text_lower) and any(b in text_lower for b in ["blur", "vision", "dizziness", "dudu", "eye turn"])):
            danger_signs.append("Pre-Eclampsia / Impending Eclampsia")
        if any(w in text_lower for w in ["baby not moving", "stop kick", "pikin no dey kick", "omo o gbon", "jariri baya motsi"]):
            danger_signs.append("Decreased or Absent Fetal Movements")
        if any(w in text_lower for w in ["fever", "chills", "ara gbona", "zazzabi", "ahu oku"]) and any(s in text_lower for s in ["smell", "discharge", "foul", "abdominal"]):
            danger_signs.append("Suspected Chorioamnionitis or Puerperal Sepsis")
        if any(w in text_lower for w in ["severe belly pain", "severe abdominal", "inu rirun to le", "hard belly"]):
            danger_signs.append("Severe Abdominal Pain (Suspected Abruption or Ectopic)")

        # Catalog of maternal symptoms
        maternal_symptoms = [
            ("Vaginal Bleeding", ["bleed", "blood", "eje", "spotting", "zubar jini"]),
            ("Severe Headache", ["headache", "ori fifo", "ciwon kai", "isi owuwa", "head dey pain"]),
            ("Blurred Vision", ["blur", "vision", "dizziness", "dudu", "eye turn"]),
            ("High Fever", ["fever", "ara gbona", "zazzabi", "ahu oku", "hot body"]),
            ("Persistent Vomiting", ["vomit", "eebi", "amai", "throw up", "onunu"]),
            ("Abdominal Pain / Cramping", ["stomach pain", "abdominal pain", "inu rirun", "ciwon ciki", "belle pain", "cramp"]),
            ("Swollen Feet / Face", ["swollen", "swelling", "edema", "ese wu", "kumburi"]),
            ("Reduced Fetal Movement", ["not moving", "pikin no kick", "omo o gbon", "stop moving"]),
            ("Fatigue / Weakness", ["weakness", "tired", "aare", "gajiya"]),
            ("Heartburn", ["heartburn", "acid", "inun gbigbona"])
        ]

        found_symptoms = []
        for sym_title, keywords in maternal_symptoms:
            if any(k in text_lower for k in keywords):
                found_symptoms.append(sym_title)

        if not found_symptoms:
            found_symptoms = ["Routine Antenatal Inquiry / General Consultation"]

        # Severity
        severity = "Mild"
        if danger_signs or any(w in text_lower for w in ["severe", "unbearable", "emergency", "too much", "heavy"]):
            severity = "Severe"
        elif any(w in text_lower for w in ["moderate", "persistent", "frequent", "high"]):
            severity = "Moderate"

        # Duration
        duration_match = re.search(r"(\d+\s*(?:day|hour|week|month)s?|since\s+\w+)", text_lower)
        duration = duration_match.group(1).title() if duration_match else "Recent onset"

        # Chief Complaint
        if danger_signs:
            chief = danger_signs[0]
        else:
            chief = found_symptoms[0] if found_symptoms else "Maternal Health Checkup"

        return ClinicalExtraction(
            chief_complaint=chief,
            symptoms=found_symptoms,
            duration=duration,
            severity=severity,
            language_detected="English / Nigerian Multilingual",
            gestational_stage=stage,
            is_pregnant=True,
            danger_signs=danger_signs,
            guideline_context=guideline_context
        )
