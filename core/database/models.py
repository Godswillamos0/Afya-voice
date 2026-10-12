import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, JSON, Enum, Uuid as UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Patient(Base):
    __tablename__ = 'patients'

    patient_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_msisdn_hash = Column(String, unique=True, index=True, nullable=False)
    preferred_lang = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    sessions = relationship("TriageSession", back_populates="patient")
    subscriptions = relationship("Subscription", back_populates="patient")


class TriageSession(Base):
    __tablename__ = 'triage_sessions'

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.patient_id'), nullable=False)
    detected_language = Column(String, nullable=True)
    triage_level = Column(String, nullable=True)  # RED, AMBER, GREEN, BLUE
    chief_complaint_raw = Column(String, nullable=True)
    snomed_concept_code = Column(String, nullable=True)
    status = Column(String, default="ACTIVE") # ACTIVE, CLOSED
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="sessions")
    audio_logs = relationship("SessionAudioLog", back_populates="session")
    escalation = relationship("DoctorEscalation", back_populates="session", uselist=False)


class Subscription(Base):
    __tablename__ = 'subscriptions'

    sub_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.patient_id'), nullable=False)
    tier_type = Column(String, nullable=False) # INSTANT_100, WEEKLY_300, FAMILY_1000, GP_ESCALATION_1200
    valid_until = Column(DateTime, nullable=False)
    status = Column(String, default="ACTIVE")
    payment_channel = Column(String, nullable=False) # DCB_MTN, DCB_AIRTEL, USSD, CARD

    patient = relationship("Patient", back_populates="subscriptions")
    transactions = relationship("Transaction", back_populates="subscription")


class Transaction(Base):
    __tablename__ = 'transactions'

    tx_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sub_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.sub_id'), nullable=False)
    amount_kobo = Column(Integer, nullable=False)
    currency = Column(String, default="NGN")
    gateway_ref = Column(String, unique=True, nullable=False)
    status = Column(String, nullable=False) # SUCCESS, FAILED
    ledger_timestamp = Column(DateTime, default=datetime.utcnow)

    subscription = relationship("Subscription", back_populates="transactions")


class SessionAudioLog(Base):
    __tablename__ = 'session_audio_logs'

    audio_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('triage_sessions.session_id'), nullable=False)
    storage_s3_path = Column(String, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    acoustic_snr_db = Column(Float, nullable=True)
    transcript_native = Column(String, nullable=True)
    transcript_english = Column(String, nullable=True)
    direction = Column(String, nullable=False) # IN, OUT

    session = relationship("TriageSession", back_populates="audio_logs")


class DoctorEscalation(Base):
    __tablename__ = 'doctor_escalations'

    escalation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('triage_sessions.session_id'), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), nullable=False) # Foreign key to a doctors table not defined here
    call_duration_secs = Column(Integer, nullable=True)
    clinical_soap_note = Column(String, nullable=True)
    disposition_code = Column(String, nullable=True)

    session = relationship("TriageSession", back_populates="escalation")
    prescription = relationship("Prescription", back_populates="escalation", uselist=False)


class Prescription(Base):
    __tablename__ = 'prescriptions'

    prescription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escalation_id = Column(UUID(as_uuid=True), ForeignKey('doctor_escalations.escalation_id'), nullable=False)
    medication_json = Column(JSON, nullable=False)
    digital_signature = Column(String, nullable=False)
    token_hash = Column(String, nullable=False)
    dispensed_status = Column(Boolean, default=False)

    escalation = relationship("DoctorEscalation", back_populates="prescription")
