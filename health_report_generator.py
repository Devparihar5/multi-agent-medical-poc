from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
import markdown
import weasyprint
from datetime import datetime
from duckduckgo_search import DDGS
from config import Config
import tempfile
import os

class HealthReportState:
    def __init__(self):
        self.patient_data = {}
        self.retrieved_data = ""
        self.nlp_findings = ""
        self.clinical_reasoning = ""
        self.validated_info = ""
        self.final_report = ""

class HealthReportGenerator:
    def __init__(self, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model=Config.MODEL_NAME,
            google_api_key=api_key,
            temperature=Config.TEMPERATURE
        )
        self.graph = self._build_graph()
    
    def _build_graph(self):
        workflow = StateGraph(dict)
        
        workflow.add_node("retriever", self._retriever_agent)
        workflow.add_node("nlp_processor", self._nlp_agent)
        workflow.add_node("reasoner", self._reasoning_agent)
        workflow.add_node("validator", self._validation_agent)
        workflow.add_node("report_generator", self._report_generator_agent)
        
        workflow.set_entry_point("retriever")
        workflow.add_edge("retriever", "nlp_processor")
        workflow.add_edge("nlp_processor", "reasoner")
        workflow.add_edge("reasoner", "validator")
        workflow.add_edge("validator", "report_generator")
        workflow.add_edge("report_generator", END)
        
        return workflow.compile()
    
    def _retriever_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates data retrieval from EHRs and databases"""
        patient_data = state["patient_data"]
        
        prompt = f"""
        As a medical data retriever, organize and structure the following patient information:
        
        Patient: {patient_data['patient_name']}, Age: {patient_data['patient_age']}
        Lab Results: {patient_data['lab_results']}
        Genetic Data: {patient_data['genetic_data']}
        Medical History: {patient_data['medical_history']}
        
        Provide a structured summary of all available data.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state["retrieved_data"] = response.content
        return state
    
    def _nlp_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts critical findings using medical NLP"""
        prompt = f"""
        As a medical NLP specialist, analyze the following patient data and extract:
        1. Critical lab abnormalities
        2. Significant genetic markers
        3. Key medical history points
        4. Risk factors
        
        Patient Data: {state['retrieved_data']}
        
        Focus on clinically significant findings only.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state["nlp_findings"] = response.content
        return state
    
    def _reasoning_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Provides clinical reasoning and risk assessment"""
        prompt = f"""
        As a clinical reasoning specialist, interpret these findings:
        
        {state['nlp_findings']}
        
        Provide:
        1. Clinical interpretation of abnormal values
        2. Risk assessment (low/moderate/high)
        3. Potential diagnoses or conditions to monitor
        4. Recommended follow-up actions
        
        Be precise and evidence-based.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state["clinical_reasoning"] = response.content
        return state
    
    def _validation_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validates medical information using web search"""
        findings = state["clinical_reasoning"]
        
        # Extract key medical terms for validation
        search_terms = []
        if "diabetes" in findings.lower():
            search_terms.append("diabetes HbA1c normal range")
        if "cholesterol" in findings.lower():
            search_terms.append("cholesterol levels normal range")
        if "hypertension" in findings.lower():
            search_terms.append("blood pressure normal range")
        
        validated_info = ""
        try:
            ddgs = DDGS()
            for term in search_terms[:Config.MAX_SEARCH_TERMS]:
                results = ddgs.text(term, max_results=Config.MAX_SEARCH_RESULTS)
                if results:
                    validated_info += f"Reference: {results[0]['body'][:200]}...\n"
        except:
            validated_info = "Unable to validate information online."
        
        state["validated_info"] = validated_info
        return state
        """Generates final patient-friendly report"""
        patient_data = state["patient_data"]
        current_date = datetime.now().strftime("%B %d, %Y")
        
        prompt = f"""
        Generate a comprehensive, patient-friendly health report for:
        Patient: {patient_data['patient_name']},
        Age: {patient_data['patient_age']}
        Report Date: {current_date}
        
        Based on:
        Clinical Findings: {state['nlp_findings']}
        Medical Reasoning: {state['clinical_reasoning']}
        
        Structure the report with:
        # Health Report Summary
        **Date:** {current_date}
        **Patient:** {patient_data['patient_name']}
        **Age:** {patient_data['patient_age']}
        
        ## Key Findings
        ## Risk Assessment
        ## Recommendations
        ## Next Steps
        
        Use clear, understandable language while maintaining medical accuracy.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state["final_report"] = response.content
        return state
    
    def generate_report(self, patient_data: Dict[str, Any]) -> str:
        """Main method to generate health report"""
        initial_state = {"patient_data": patient_data}
        result = self.graph.invoke(initial_state)
        return result["final_report"]
    
    def generate_pdf_report(self, report_content: str, patient_name: str) -> str:
        """Generate PDF version of the report using markdown"""
        temp_dir = tempfile.gettempdir()
        filename = os.path.join(temp_dir, f"{patient_name.replace(' ', '_')}_health_report.pdf")
        
        # Convert markdown to HTML
        html = markdown.markdown(report_content)
        
        # Add CSS styling
        styled_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                ul {{ margin: 15px 0; }}
                li {{ margin: 8px 0; }}
                strong {{ color: #e74c3c; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        # Convert HTML to PDF
        weasyprint.HTML(string=styled_html).write_pdf(filename)
        return filename
    def _report_generator_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generates final patient-friendly report"""
        patient_data = state["patient_data"]
        current_date = datetime.now().strftime("%B %d, %Y")
        
        prompt = f"""
        Generate a CONCISE, SPECIFIC medical report. Only include sections with actual findings.
        
        Patient: {patient_data['patient_name']},
        Age: {patient_data['patient_age']}
        Report Date: {current_date}
        
        Clinical Findings: {state['nlp_findings']}
        Medical Analysis: {state['clinical_reasoning']}
        Validated Info: {state['validated_info']}
        
        STRICT REQUIREMENTS:
        - Be factual and specific - NO generic encouragement or support statements
        - Only include sections that have actual data/findings
        - Use exact values and ranges
        - No "we are here to support you" type language
        - Focus on medical facts only
        
        Structure (only include sections with data):
        # Medical Report
        **Date:** {current_date} \n
        **Patient:** {patient_data['patient_name']}, \n
        **Age** {patient_data['patient_age']} 
        
        ## Lab Results Analysis
        (Only if abnormal values found)
        
        ## Risk Factors
        (Only if specific risks identified)
        
        ## Clinical Recommendations
        (Only specific, actionable medical recommendations)
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state["final_report"] = response.content
        return state
