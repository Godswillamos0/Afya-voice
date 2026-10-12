from pydantic import BaseModel, Field, UUID4
from typing import List, Optional
from datetime import datetime
from enum import Enum


class LanguageCode(str, Enum):
    YORUBA = "yo"
    HAUSA = "ha"
    IGBO = "ig"
    PIDGIN = "pcm"
    ENGLISH = "en-NG"


class RiskColor(str, Enum):
    RED = "RED"
    AMBER = "AMBER"
    GREEN = "GREEN"
    BLUE = "BLUE"


class RecommendationType(str, Enum):
    IMMEDIATE_HOSPITAL_DISPATCH = "IMMEDIATE_HOSPITAL_DISPATCH"
    DOCTOR_TELECONSULT_BOOKING = "DOCTOR_TELECONSULT_BOOKING"
    HOME_CARE_OTC_PROTOCOL = "HOME_CARE_OTC_PROTOCOL"
    ROUTINE_EDUCATION = "ROUTINE_EDUCATION"


class DetectedLanguage(BaseModel):
    iso_code: LanguageCode
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    dialect_region: str


class TriageAssessment(BaseModel):
    manchester_level: int = Field(..., ge=1, le=4)
    risk_color: RiskColor
    emergency_red_flag_detected: bool
    red_flag_details: Optional[List[str]] = None
    recommendation_type: RecommendationType


class Symptom(BaseModel):
    name: str
    snomed_id: str
    duration_hours: float
    severity_score: int = Field(..., ge=1, le=10)


class PatientMetrics(BaseModel):
    age_years: Optional[float] = None
    is_pediatric: Optional[bool] = None
    is_pregnant: Optional[bool] = None
    known_allergies: Optional[List[str]] = None


class ClinicalEntities(BaseModel):
    chief_complaint: str
    symptoms: List[Symptom]
    patient_metrics: Optional[PatientMetrics] = None


class NATLASClinicalTriagePayload(BaseModel):
    session_id: UUID4
    timestamp_utc: datetime
    detected_language: DetectedLanguage
    triage_assessment: TriageAssessment
    clinical_entities: ClinicalEntities


class TelcoOperator(str, Enum):
    MTN_NG = "MTN_NG"
    AIRTEL_NG = "AIRTEL_NG"
    GLO_NG = "GLO_NG"
    NINE_MOBILE_NG = "9MOBILE_NG"


class SubscriptionPlan(str, Enum):
    INSTANT_100 = "INSTANT_100"
    WEEKLY_300 = "WEEKLY_300"
    FAMILY_1000 = "FAMILY_1000"
    GP_ESCALATION_1200 = "GP_ESCALATION_1200"


class WebhookStatus(str, Enum):
    SUCCESS = "SUCCESS"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    USER_TIMEOUT = "USER_TIMEOUT"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class TelcoDCBBillingWebhook(BaseModel):
    transaction_id: UUID4
    telco_operator: TelcoOperator
    msisdn_masked: str
    amount_debited_kobo: int
    currency: str = "NGN"
    subscription_plan: Optional[SubscriptionPlan] = None
    status: WebhookStatus
    timestamp: datetime
    hmac_signature: str
