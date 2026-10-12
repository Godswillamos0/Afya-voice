import hashlib
import uuid
from typing import Optional
from core.database.session import SessionLocal
from core.database.models import Patient, TriageSession, SessionAudioLog
from services.llm.clinical_parser import ClinicalExtraction
from services.triage.engine import TriageAssessment

class DatabaseSessionManager:
    """
    Manages persistence of incoming patient sessions, N-ATLAS transcriptions,
    and clinical triage outcomes.
    """

    @staticmethod
    def _hash_phone(phone: str) -> str:
        """Hash phone number to comply with NDPC / HIPAA data privacy requirements."""
        return hashlib.sha256(phone.strip().encode()).hexdigest()

    def record_triage_session(
        self,
        phone_number: str,
        audio_path: str,
        transcript_text: str,
        clinical_data: ClinicalExtraction,
        triage_assessment: TriageAssessment
    ) -> Optional[uuid.UUID]:
        db = SessionLocal()
        try:
            phone_hash = self._hash_phone(phone_number)

            # 1. Find or create Patient
            patient = db.query(Patient).filter(Patient.phone_msisdn_hash == phone_hash).first()
            if not patient:
                patient = Patient(
                    patient_id=uuid.uuid4(),
                    phone_msisdn_hash=phone_hash,
                    preferred_lang=clinical_data.language_detected or "English",
                    is_active=True
                )
                db.add(patient)
                db.flush()

            # 2. Create Triage Session
            session = TriageSession(
                session_id=uuid.uuid4(),
                patient_id=patient.patient_id,
                detected_language=clinical_data.language_detected or "English",
                triage_level=triage_assessment.urgency_tier,
                chief_complaint_raw=clinical_data.chief_complaint,
                snomed_concept_code=triage_assessment.snomed_concept_code,
                status="ACTIVE"
            )
            db.add(session)
            db.flush()

            # 3. Create Session Audio Log
            audio_log = SessionAudioLog(
                audio_id=uuid.uuid4(),
                session_id=session.session_id,
                storage_s3_path=audio_path,
                duration_seconds=5.0,  # approximate default
                transcript_native=transcript_text,
                transcript_english=transcript_text,
                direction="IN"
            )
            db.add(audio_log)

            db.commit()
            print(f"[DB] Triage session recorded in database! (Session ID: {session.session_id})")
            return session.session_id

        except Exception as e:
            db.rollback()
            print(f"[DB ERROR] Database recording error: {str(e)}")
            return None
        finally:
            db.close()
