from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class SNOMEDConcept:
    concept_id: str             # Official SNOMED CT Concept ID
    fsn: str                    # Fully Specified Name
    display_name: str           # Clinical Display Name
    mts_discriminator: str      # Manchester Triage System Discriminator
    default_tier: str           # RED, YELLOW, GREEN, WHITE
    aliases: List[str] = field(default_factory=list) # Multilingual expressions (EN, Pidgin, Yoruba, Hausa, Igbo)

class SNOMEDRegistry:
    """
    Sovereign SNOMED CT Concept Registry & Multilingual Terminology Service.
    Maps patient complaints in English, Nigerian Pidgin, Yoruba, Hausa, and Igbo
    to standardized SNOMED CT identifiers and MTS discriminators.
    """

    CONCEPTS: List[SNOMEDConcept] = [
        # RED / EMERGENCY CONCEPTS
        SNOMEDConcept(
            concept_id="29857009",
            fsn="Chest pain (finding)",
            display_name="Chest Pain",
            mts_discriminator="CARDIAC_CHEST_PAIN",
            default_tier="RED",
            aliases=["chest pain", "chest tightness", "pain for chest", "pressure in chest", "aiya n dun mi", "ciwon kirji", "obi m na-afu m ufu"]
        ),
        SNOMEDConcept(
            concept_id="267036007",
            fsn="Dyspnea (finding)",
            display_name="Difficulty Breathing / Dyspnea",
            mts_discriminator="INADEQUATE_BREATHING",
            default_tier="RED",
            aliases=["difficulty breathing", "shortness of breath", "breathlessness", "cannot breathe", "gasping", "mi o le mi daada", "numfashi da wuya", "iku ume na-esiri m ike", "no fit breathe"]
        ),
        SNOMEDConcept(
            concept_id="131148009",
            fsn="Bleeding (finding)",
            display_name="Severe Hemorrhage / Bleeding",
            mts_discriminator="EXSANGUINATING_HEMORRHAGE",
            default_tier="RED",
            aliases=["severe bleeding", "heavy bleeding", "hemorrhage", "gushing blood", "blood dey rush", "eje n san pupo", "zubar jini"]
        ),
        SNOMEDConcept(
            concept_id="91175000",
            fsn="Seizure (finding)",
            display_name="Convulsion / Seizure",
            mts_discriminator="ACTIVE_CONVULSION",
            default_tier="RED",
            aliases=["convulsion", "seizure", "fitting", "jerking", "farfadiya", "warapa", "akwukwu"]
        ),
        SNOMEDConcept(
            concept_id="422768005",
            fsn="Unconsciousness (finding)",
            display_name="Loss of Consciousness / Syncope",
            mts_discriminator="UNRESPONSIVENESS",
            default_tier="RED",
            aliases=["unconscious", "unconsciousness", "passed out", "fainted", "collapsed", "o daku", "sume", "onweghi onwe ya"]
        ),
        SNOMEDConcept(
            concept_id="230690007",
            fsn="Stroke (disorder)",
            display_name="Acute Stroke / Hemiplegia",
            mts_discriminator="ACUTE_STROKE_SYMPTOMS",
            default_tier="RED",
            aliases=["stroke", "paralysis", "face drooping", "one side weak", "apakan ara ro", "shanyewar jiki"]
        ),

        # YELLOW / URGENT CONCEPTS
        SNOMEDConcept(
            concept_id="386661006",
            fsn="Fever (finding)",
            display_name="Fever / Hyperpyrexia",
            mts_discriminator="HIGH_FEVER_PERSISTENT",
            default_tier="YELLOW",
            aliases=["fever", "high fever", "hot body", "body dey hot", "temperature", "zazzabi", "iba", "ahu oku"]
        ),
        SNOMEDConcept(
            concept_id="21522001",
            fsn="Abdominal pain (finding)",
            display_name="Abdominal Pain",
            mts_discriminator="SEVERE_ABDOMINAL_PAIN",
            default_tier="YELLOW",
            aliases=["abdominal pain", "severe stomach pain", "stomach ache", "belly pain", "inun run", "ciwon ciki", "afo ogwugwu"]
        ),
        SNOMEDConcept(
            concept_id="422400008",
            fsn="Vomiting (finding)",
            display_name="Persistent Vomiting",
            mts_discriminator="PERSISTENT_VOMITING_DEHYDRATION",
            default_tier="YELLOW",
            aliases=["vomiting", "persistent vomiting", "throwing up", "dey vomit", "amai", "gbi", "agbo"]
        ),
        SNOMEDConcept(
            concept_id="62315008",
            fsn="Diarrhea (finding)",
            display_name="Acute Diarrhea / Dehydration Risk",
            mts_discriminator="PERSISTENT_VOMITING_DEHYDRATION",
            default_tier="YELLOW",
            aliases=["diarrhea", "watery stool", "running stomach", "purging", "igbe gbuuru", "zawo", "otoro"]
        ),
        SNOMEDConcept(
            concept_id="125593007",
            fsn="Injury of bone (disorder)",
            display_name="Fracture / Severe Trauma",
            mts_discriminator="SIGNIFICANT_TRAUMA_FRACTURE",
            default_tier="YELLOW",
            aliases=["fracture", "broken bone", "dislocation", "deep cut", "severe burn", "egbo nla", "karye kashi"]
        ),

        # GREEN / ROUTINE CONCEPTS
        SNOMEDConcept(
            concept_id="25064002",
            fsn="Headache (finding)",
            display_name="Headache / Cephalea",
            mts_discriminator="MILD_HEADACHE",
            default_tier="GREEN",
            aliases=["headache", "head pain", "head dey pain", "ciwon kai", "ori n fo mi", "isi owuwa"]
        ),
        SNOMEDConcept(
            concept_id="49727002",
            fsn="Cough (finding)",
            display_name="Cough",
            mts_discriminator="MILD_UPPER_RESPIRATORY_TRACT",
            default_tier="GREEN",
            aliases=["cough", "coughing", "dry cough", "tari", "iko", "uko"]
        ),
        SNOMEDConcept(
            concept_id="64531003",
            fsn="Rhinorrhea (finding)",
            display_name="Runny Nose / Rhinorrhea",
            mts_discriminator="MILD_UPPER_RESPIRATORY_TRACT",
            default_tier="GREEN",
            aliases=["runny nose", "catarrh", "sneezing", "cold", "majina", "otutu"]
        ),
        SNOMEDConcept(
            concept_id="367391008",
            fsn="Malaise (finding)",
            display_name="General Malaise / Fatigue",
            mts_discriminator="GENERAL_MALAISE",
            default_tier="GREEN",
            aliases=["malaise", "fatigue", "tiredness", "weakness", "body pain", "ara didun", "gajiya", "ike ogwugwu"]
        ),
        SNOMEDConcept(
            concept_id="162397003",
            fsn="Pain in throat (finding)",
            display_name="Sore Throat / Pharyngitis",
            mts_discriminator="MILD_UPPER_RESPIRATORY_TRACT",
            default_tier="GREEN",
            aliases=["sore throat", "throat pain", "pain when swallowing", "ona ofun dun mi", "ciwon makogwaro"]
        )
    ]

    @classmethod
    def resolve_symptoms(cls, text: str) -> List[SNOMEDConcept]:
        """
        Scans clinical text or symptom list and returns matching standardized SNOMED CT concepts.
        """
        text_lower = text.lower()
        matched: List[SNOMEDConcept] = []
        seen_ids = set()

        for concept in cls.CONCEPTS:
            for alias in concept.aliases:
                if alias in text_lower:
                    if concept.concept_id not in seen_ids:
                        matched.append(concept)
                        seen_ids.add(concept.concept_id)
                    break
        return matched
