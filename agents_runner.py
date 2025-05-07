from langchain.agents import Tool, initialize_agent
from langchain.llms import OpenAI  # or use HuggingFaceHub or Groq
from agent_tools import query_patient_data, check_risk_factors
import os
from dotenv import load_dotenv

load_dotenv()
llm = OpenAI(temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))

tools = [
    Tool(name="QueryPatientData", func=lambda x: query_patient_data(int(x.split()[-1])), description="Fetch patient's labs and diagnoses"),
    Tool(name="CheckRiskFactors", func=lambda x: check_risk_factors(int(x.split()[-1])), description="Check if lab values are risky"),
]

agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

def run_agent(input_text):
    return agent.run(input_text)