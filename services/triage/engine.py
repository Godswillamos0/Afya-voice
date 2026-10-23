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
    snomed_concept_code: str       # Primary SNOMED CT Concept ID
    snomed_display_name: str       # Official Clinical Display Name
    discriminators_triggered: List[str] = field(default_factory=list)
    guideline_source: str = "WHO / Nigeria FMOH Guidelines"

class TriageEngine:
    """
    Sovereign Maternal Clinical Decision Support Engine.
    Evaluates obstetric risk using the Manchester Triage System (MTS) adapted for
    WHO Integrated Management of Pregnancy & Childbirth (PCPNC) and FMOH Nigeria Maternal Guidelines.
    """

    def __init__(self):
        config_path = os.path.join(os.getcwd(), "config", "mts_protocols.json")
        self.protocols = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.protocols = json.load(f)

    def evaluate(self, clinical_data: ClinicalExtraction, patient_name: str = "Mama") -> TriageAssessment:
        complaint = clinical_data.chief_complaint or ""
        symptoms = clinical_data.symptoms or []
        combined_text = f"{complaint} {' '.join(symptoms)} {' '.join(clinical_data.danger_signs)}"
        severity = (clinical_data.severity or "Moderate").title()
        stage = clinical_data.gestational_stage or "Pregnancy"

        # Step 1: Map to standardized SNOMED CT concepts
        matched_concepts = SNOMEDRegistry.resolve_symptoms(combined_text)

        if not matched_concepts:
            primary_snomed = SNOMEDConcept(
                concept_id="424441002",
                fsn="Antenatal care (procedure)",
                display_name="Routine Antenatal Care (ANC)",
                mts_discriminator="ROUTINE_CARE",
                default_tier="GREEN"
            )
            matched_concepts = [primary_snomed]
        else:
            primary_snomed = matched_concepts[0]

        # Step 2: Obstetric Danger Signs Assessment
        has_red = False
        has_yellow = False

        # Cardinal Obstetric Danger Signs are ALWAYS RED in pregnancy
        if clinical_data.danger_signs:
            has_red = True

        for c in matched_concepts:
            if c.default_tier == "RED":
                has_red = True
            elif c.default_tier == "YELLOW":
                has_yellow = True

        # Severe headache, severe chest pain, or bleeding in pregnancy is RED
        if severity == "Severe" and any(w in combined_text.lower() for w in ["headache", "ori fifo", "bleed", "eje", "fever", "cramp"]):
            has_red = True

        triggered_discriminators = [c.mts_discriminator for c in matched_concepts]
        if clinical_data.danger_signs:
            triggered_discriminators.extend(clinical_data.danger_signs)

        # Step 3: Determine Urgency Tier
        if has_red:
            tier = "RED"
            title = "🔴 OBSTETRIC EMERGENCY (IMMEDIATE HOSPITAL ATTENTION)"
            desc = "Life-threatening obstetric danger signs identified requiring urgent emergency care."
            action = "Proceed immediately to the nearest General Hospital, CEmONC Maternity Center, or call Emergency (112)."
        elif has_yellow:
            tier = "YELLOW"
            title = "🟡 URGENT MATERNAL REVIEW (WITHIN 12–24 HOURS)"
            desc = "Clinical symptoms requiring prompt medical evaluation at your registered Primary Health Center."
            action = "Visit your Primary Health Center (PHC) or antenatal clinic today for clinical examination."
        else:
            tier = "GREEN"
            title = "🟢 ROUTINE ANTENATAL CARE & HOME GUIDANCE"
            desc = "Common physiological pregnancy symptoms or routine antenatal inquiry."
            action = "Continue your regular antenatal visits, take prescribed routine supplements, and monitor your symptoms."

        # Step 4: Construct Patient Communication Message with Guideline Citations
        symptom_list_str = ", ".join(clinical_data.symptoms) if clinical_data.symptoms else clinical_data.chief_complaint
        
        message = (
            f"🤰 *AfyaMama Maternal Triage & Care Plan*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *URGENCY LEVEL:* {title}\n"
            f"⏱ *Stage:* {stage} • *Onset:* {clinical_data.duration}\n\n"
            f"📋 *Clinical Findings:*\n"
            f"• *Chief Issue:* {clinical_data.chief_complaint}\n"
            f"• *Reported Symptoms:* {symptom_list_str}\n"
            f"• *SNOMED CT Concept:* {primary_snomed.display_name} (`{primary_snomed.concept_id}`)\n\n"
        )

        if clinical_data.danger_signs:
            danger_str = "\n".join([f"  ⚠️ {d}" for d in clinical_data.danger_signs])
            message += f"🚨 *CRITICAL OBSTETRIC DANGER SIGNS DETECTED:*\n{danger_str}\n\n"

        message += f"🩺 *RECOMMENDED CLINICAL ACTION:*\n{action}\n\n"

        # Evidence-Based Care Guidance & Remedies based on WHO / Nigeria Guidelines
        if tier == "RED":
            message += (
                f"🚨 *CRITICAL INSTRUCTIONS:*\n"
                f"• Do NOT take any home remedies or wait until tomorrow.\n"
                f"• Lie on your left side to maximize blood flow to your baby.\n"
                f"• Have a companion accompany you immediately to the nearest hospital with an emergency obstetric unit.\n"
                f"• Emergency Hotline: Call *112* immediately.\n\n"
            )
        elif tier == "YELLOW":
            message += (
                f"💧 *Immediate Care Steps (WHO & FMOH Nigeria Guidelines):*\n"
                f"• Hydrate with clean boiled water or Oral Rehydration Salts (ORS).\n"
                f"• Rest in a cool, well-ventilated room.\n"
                f"• If you have fever, take only Paracetamol (avoid Ibuprofen or Aspirin).\n"
                f"• Visit your PHC clinic today for malaria check and blood pressure measurement.\n\n"
            )
        else:
            message += (
                f"🌿 *Guideline-Approved Home Relief (WHO Antenatal Care Standards):*\n"
                f"• *For Morning Sickness / Nausea:* Eat small frequent meals rich in complex carbohydrates (dry crackers, boiled yam/sweet potatoes). Ginger tea or fresh ginger root is safe and effective.\n"
                f"• *For Mild Body Ache:* Rest with feet elevated; use paracetamol if needed.\n"
                f"• *Routine Supplements:* Remember your daily Iron (60 mg) + Folic Acid (400 µg) with clean water or citrus juice (avoid taking with tea, coffee, or milk).\n"
                f"• Sleep under your Long-Lasting Insecticide-Treated Net (LLIN) every night.\n\n"
            )

        message += f"📚 _Standard: WHO Antenatal & Emergency Obstetric Care • Nigeria FMOH MNCH Protocols • SNOMED CT_"

        return TriageAssessment(
            urgency_tier=tier,
            urgency_title=title,
            urgency_description=desc,
            action_plan=action,
            patient_message=message,
            snomed_concept_code=primary_snomed.concept_id,
            snomed_display_name=primary_snomed.display_name,
            discriminators_triggered=triggered_discriminators,
            guideline_source="WHO Antenatal & Nigeria FMOH Guidelines"
        )
