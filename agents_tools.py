from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DB_URL"))

def query_patient_data(patient_id):
    with engine.connect() as conn:
        patient = conn.execute(
            text("SELECT * FROM patients WHERE patient_id = :id"),
            {"id": patient_id}
        ).fetchone()

        labs = conn.execute(
            text("SELECT test_name, value, date FROM labs WHERE patient_id = :id"),
            {"id": patient_id}
        ).fetchall()

        diagnoses = conn.execute(
            text("SELECT diagnosis, diagnosis_date FROM diagnoses WHERE patient_id = :id"),
            {"id": patient_id}
        ).fetchall()

    return f"Patient Info: {patient}\n\nLabs: {labs}\n\nDiagnoses: {diagnoses}"

def check_risk_factors(patient_id):
    with engine.connect() as conn:
        results = conn.execute(
            text("SELECT test_name, value FROM labs WHERE patient_id = :id"),
            {"id": patient_id}
        ).fetchall()

    risks = []
    for test, value in results:
        if test == "HbA1c" and value >= 7:
            risks.append("High HbA1c (possible diabetes)")
        if test == "Cholesterol" and value > 200:
            risks.append("High cholesterol")

    return ", ".join(risks) if risks else "No major risk indicators"