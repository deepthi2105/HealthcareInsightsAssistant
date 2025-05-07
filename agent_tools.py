from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import streamlit as st

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

    return (
        f"PATIENT_ID: {patient_id}\n"
        f"Patient Info: {patient}\n\n"
        f"Labs: {labs}\n\n"
        f"Diagnoses: {diagnoses}"
    )

def check_risk_factors(patient_id):
    with engine.connect() as conn:
        labs = conn.execute(
            text("SELECT test_name, value FROM labs WHERE patient_id = :id"),
            {"id": patient_id}
        ).fetchall()

    risks = []
    for test, value in labs:
        if test.lower() == "hba1c" and value >= 7:
            risks.append("⚠️ High HbA1c (possible diabetes)")
        if test.lower() == "cholesterol" and value > 200:
            risks.append("⚠️ High cholesterol")

    return ", ".join(risks) if risks else "✅ No major risk indicators"

def query_medications(patient_id):
    with engine.connect() as conn:
        meds = conn.execute(
            text("SELECT drug_name, dose, start_date, end_date FROM medications WHERE patient_id = :id"),
            {"id": patient_id}
        ).fetchall()

    return f"Medications for patient {patient_id}: {meds or 'No data found'}"

def query_visits(patient_id):
    with engine.connect() as conn:
        visits = conn.execute(
            text("SELECT visit_date, department, physician, reason FROM visits WHERE patient_id = :id"),
            {"id": patient_id}
        ).fetchall()

    return f"Visit history for patient {patient_id}: {visits or 'No visit history available'}"

def analyze_trends_summary(patient_id, test_name=None):
    with engine.connect() as conn:
        if test_name:
            query = text("""
                SELECT test_name, value, date FROM labs
                WHERE patient_id = :id AND test_name = :test
                ORDER BY date
            """)
            results = conn.execute(query, {"id": patient_id, "test": test_name}).fetchall()
        else:
            query = text("""
                SELECT test_name, value, date FROM labs
                WHERE patient_id = :id
                ORDER BY test_name, date
            """)
            results = conn.execute(query, {"id": patient_id}).fetchall()

    if not results:
        return f"❌ No lab data found for patient {patient_id}" + (f" and test '{test_name}'" if test_name else "")

    trends = defaultdict(list)
    for test, val, date in results:
        trends[test].append((date, float(val)))

    summaries = []
    for test, data in trends.items():
        data.sort()
        first_val, last_val = data[0][1], data[-1][1]
        delta = last_val - first_val
        direction = "increased" if delta > 0 else "decreased" if delta < 0 else "remained stable"
        points = "\n".join([f"  - {d.strftime('%Y-%m-%d')}: {v:.1f}" for d, v in data])
        summaries.append(
            f"📊 **{test} Trends**:\n{points}\n🔍 {test} has {direction} by {abs(delta):.1f} over the period.\n"
        )

    return "\n".join(summaries)

def suggest_lifestyle_changes(patient_id):
    with engine.connect() as conn:
        diagnoses = conn.execute(
            text("SELECT diagnosis FROM diagnoses WHERE patient_id = :id"),
            {"id": patient_id}
        ).fetchall()

        labs = conn.execute(
            text("SELECT test_name, value FROM labs WHERE patient_id = :id"),
            {"id": patient_id}
        ).fetchall()

    diagnosis_set = {d[0].lower() for d in diagnoses}
    lab_dict = {test.lower(): float(val) for test, val in labs}

    suggestions = []

    if "type 2 diabetes" in diagnosis_set or lab_dict.get("hba1c", 0) >= 6.5:
        suggestions.append("• Reduce sugar and refined carb intake.")
        suggestions.append("• Exercise 30 minutes daily (e.g., walking, cycling).")
        suggestions.append("• Consider a Mediterranean or DASH diet.")

    if "hypertension" in diagnosis_set or lab_dict.get("cholesterol", 0) >= 200:
        suggestions.append("• Reduce sodium to less than 1500 mg/day.")
        suggestions.append("• Avoid processed foods; eat fruits, vegetables, whole grains.")
        suggestions.append("• Manage stress using relaxation or mindfulness techniques.")

    if "hyperlipidemia" in diagnosis_set:
        suggestions.append("• Limit saturated fats and increase fiber intake.")
        suggestions.append("• Engage in regular aerobic exercise.")
        suggestions.append("• Consider omega-3 fatty acids through diet or supplements.")

    if "obesity" in diagnosis_set:
        suggestions.append("• Monitor calorie intake and engage in weight-loss planning.")
        suggestions.append("• Incorporate strength training twice a week.")

    if not suggestions:
        return "✅ No critical health risks identified. Maintain a balanced diet and regular activity."

    return "🧠 **Lifestyle Recommendations:**\n" + "\n".join(suggestions)

def extract_test_name(query):
    test_keywords = ["HbA1c", "Cholesterol", "LDL", "HDL", "Triglycerides", "Glucose"]
    for keyword in test_keywords:
        if keyword.lower() in query.lower():
            return keyword
    return None
