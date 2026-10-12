import os
import json
from dataclasses import dataclass, field
from typing import List, Optional
from services.llm.clinical_parser import ClinicalExtraction
from services.triage.snomed_registry import SNOMEDRegistry, SNOMEDConcept

@dataclass
class TriageAssessment:
    urgency_tier: str              # RED, YELLOW, GREEN, WHITE
    urgency_title: str
    urgency_description: str
    action_plan: str
    patient_message: str
    snomed_concept_code: str       # Primary SNOMED CT Concept ID (e.g., 29857009)
    snomed_display_name: str       # Official Clinical Display Name
    discriminators_triggered: List[str] = field(default_factory=list)

class TriageEngine:
    """
    Enterprise Clinical Decision Support Engine.
    Combines the Manchester Triage System (MTS) protocol matrix with 
    SNOMED CT clinical concept mapping, replacing hardcoded string checks.
    """

    def __init__(self):
        config_path = os.path.join(os.getcwd(), "config", "mts_protocols.json")
        self.protocols = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.protocols = json.load(f)

    def evaluate(self, clinical_data: ClinicalExtraction, patient_name: str = "Patient") -> TriageAssessment:
        complaint = clinical_data.chief_complaint or ""
        symptoms = clinical_data.symptoms or []
        combined_text = f"{complaint} {' '.join(symptoms)}"
        severity = (clinical_data.severity or "Moderate").title()

        # Step 1: Map patient complaint into standardized SNOMED CT concepts
        matched_concepts = SNOMEDRegistry.resolve_symptoms(combined_text)

        # Fallback if no specific concept matched
        if not matched_concepts:
            primary_snomed = SNOMEDConcept(
                concept_id="367391008",
                fsn="Malaise (finding)",
                display_name="General Malaise",
                mts_discriminator="GENERAL_MALAISE",
                default_tier="GREEN"
            )
            matched_concepts = [primary_snomed]
        else:
            primary_snomed = matched_concepts[0]

        # Step 2: Evaluate Manchester Triage System Priority Matrix
        # Hierarchy: RED (Priority 1) > YELLOW (Priority 2) > GREEN (Priority 3) > WHITE (Priority 4)
        has_red = any(c.default_tier == "RED" for c in matched_concepts)
        has_yellow = any(c.default_tier == "YELLOW" for c in matched_concepts)

        # Upgrade to RED if severe respiratory or severe chest indicators present
        if severity == "Severe" and any(c.concept_id in ["267036007", "29857009"] for c in matched_concepts):
            has_red = True

        triggered_discriminators = [c.mts_discriminator for c in matched_concepts]

        # Determine Triage Tier from MTS Matrix
        if has_red:
            tier = "RED"
            title = "🔴 EMERGENCY (IMMEDIATE HOSPITAL ATTENTION REQUIRED)"
            desc = "Life-threatening Manchester Triage discriminators identified."
            action = "Proceed immediately to the nearest Emergency Center or call Nigeria Emergency (112)."
        elif has_yellow or severity == "Severe":
            tier = "YELLOW"
            title = "🟡 URGENT (CLINICAL REVIEW WITHIN 12-24 HOURS)"
            desc = "Urgent clinical flags requiring evaluation at a Primary Health Care center today."
            action = "Visit a registered Primary Health Care (PHC) center or hospital within 12-24 hours for examination."
        else:
            tier = "GREEN"
            title = "🟢 ROUTINE / PRIMARY CARE"
            desc = "Standard non-emergency symptoms suitable for outpatient consultation."
            action = "Schedule a routine teleconsultation or visit your local community dispensary."

        # Generate Clinical Message with Standardized SNOMED CT and MTS Metadata
        symptom_list_str = ", ".join(clinical_data.symptoms) if clinical_data.symptoms else clinical_data.chief_complaint
        
        message = (
            f"🏥 *AfyaVoice Clinical Triage Report*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *URGENCY LEVEL: {title.split(' ')[0]} {tier}*\n\n"
            f"📋 *Clinical Findings:*\n"
            f"• *Chief Complaint:* {clinical_data.chief_complaint}\n"
            f"• *Reported Symptoms:* {symptom_list_str}\n"
            f"• *Duration:* {clinical_data.duration or 'Not specified'}\n"
            f"• *Severity:* {severity}\n"
            f"• *SNOMED CT Term:* {primary_snomed.display_name} (`{primary_snomed.concept_id}`)\n\n"
            f"🩺 *CLINICAL ACTION PLAN:*\n"
            f"{action}\n\n"
        )

        if tier == "RED":
            message += f"🚨 *URGENT WARNING:* Do not delay. If you are alone, alert a family member, neighbor, or call Nigeria Emergency (*112*) immediately.\n\n"
        elif tier == "YELLOW":
            message += f"💧 *Immediate Self-Care Steps:*\n• Stay well-hydrated with clean water or ORS.\n• Rest in a well-ventilated room.\n• If symptoms suddenly worsen, seek emergency care immediately.\n\n"
        else:
            message += f"🍵 *Home Care Guidance:*\n• Ensure adequate hydration and rest.\n• Monitor symptoms over the next 24-48 hours.\n• If high fever or intense pain develops, visit your nearest clinic.\n\n"

        message += f"_MTS Protocol Standard • SNOMED CT Indexed • Powered by N-ATLAS Sovereign AI_"

        return TriageAssessment(
            urgency_tier=tier,
            urgency_title=title,
            urgency_description=desc,
            action_plan=action,
            patient_message=message,
            snomed_concept_code=primary_snomed.concept_id,
            snomed_display_name=primary_snomed.display_name,
            discriminators_triggered=triggered_discriminators
        )
