from langchain.agents import Tool, initialize_agent
from langchain.llms import OpenAI
from agent_tools import (
    query_patient_data,
    check_risk_factors,
    query_medications,
    query_visits,
    analyze_trends_summary,
    suggest_lifestyle_changes
)
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import re

load_dotenv()
llm = OpenAI(temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))
engine = create_engine(os.getenv("DB_URL"))

def resolve_patient_id(query_str):
    match = re.search(r"(?:patient\s*[:#-]?\s*|^)(\d+)", query_str, re.IGNORECASE)
    if match:
        return int(match.group(1))

    known_names = ["john doe", "jane smith", "michael patel"]
    for name in known_names:
        if name in query_str.lower():
            with engine.connect() as conn:
                res = conn.execute(
                    text("SELECT patient_id FROM patients WHERE lower(name) = :n"),
                    {"n": name}
                ).fetchone()
                if res:
                    return res[0]

    return None

tools = [
    Tool(
        name="QueryPatientData",
        func=lambda x: (
            query_patient_data(pid)
            if (pid := resolve_patient_id(x)) else "❌ Please specify a valid patient name or ID."
        ),
        description="Fetch patient demographics, labs, and diagnoses."
    ),
    Tool(
        name="CheckRiskFactors",
        func=lambda x: (
            check_risk_factors(pid)
            if (pid := resolve_patient_id(x)) else "❌ Could not determine patient ID for risk scoring."
        ),
        description="Analyze lab values for potential health risks using patient ID."
    ),
    Tool(
        name="QueryMedications",
        func=lambda x: (
            query_medications(pid)
            if (pid := resolve_patient_id(x)) else "❌ No valid patient ID or name found."
        ),
        description="Fetch medication history."
    ),
    Tool(
        name="QueryVisits",
        func=lambda x: (
            query_visits(pid)
            if (pid := resolve_patient_id(x)) else "❌ Visit data unavailable without patient info."
        ),
        description="Fetch hospital visit summaries."
    ),
    Tool(
        name="AnalyzeTrends",
        func=lambda x: (
            analyze_trends_summary(pid)
            if (pid := resolve_patient_id(x)) else "❌ Could not analyze trends without valid patient."
        ),
        description="Detect trends or patterns in lab results over time using patient ID."
    ),
    Tool(
        name="SuggestLifestyleChanges",
        func=lambda x: (
            suggest_lifestyle_changes(pid)
            if (pid := resolve_patient_id(x)) else "❌ Invalid patient reference."
        ),
        description="Suggest lifestyle or clinical advice based on labs and diagnoses."
    )
]

agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True,
    max_iterations=10
)

def run_agent(input_text):
    return agent.run(input_text)
