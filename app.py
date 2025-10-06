import streamlit as st
from health_report_generator import HealthReportGenerator
from config import Config

st.set_page_config(page_title="Patient Health Report Generator", layout="wide")

st.title("🏥 Patient Lab & Genetic Report Generator")

# Get API key from config
try:
    api_key = Config.get_gemini_api_key()
except ValueError as e:
    st.error(str(e))
    st.stop()

# Initialize generator
generator = HealthReportGenerator(api_key)

# Main interface
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Patient Data Input")
    
    patient_name = st.text_input("Patient Name", "John Doe")
    patient_age = st.number_input("Age", min_value=1, max_value=120, value=45)
    
    lab_results = st.text_area(
        "Lab Results", 
        "Glucose: 180 mg/dL (High)\nHbA1c: 8.2% (Elevated)\nCholesterol: 240 mg/dL (High)\nHDL: 35 mg/dL (Low)"
    )
    
    genetic_data = st.text_area(
        "Genetic Markers",
        "APOE4 variant present\nBRCA1: Negative\nCYP2D6: Poor metabolizer"
    )
    
    medical_history = st.text_area(
        "Medical History",
        "Type 2 Diabetes diagnosed 2020\nHypertension\nFamily history of heart disease"
    )

with col2:
    st.header("Generated Report")
    
    if st.button("Generate Report", type="primary"):
        with st.spinner("Generating comprehensive health report..."):
            try:
                report = generator.generate_report({
                    "patient_name": patient_name,
                    "patient_age": patient_age,
                    "lab_results": lab_results,
                    "genetic_data": genetic_data,
                    "medical_history": medical_history
                })
                
                st.success("Report generated successfully!")
                st.markdown(report)
                
                # Generate PDF
                pdf_path = generator.generate_pdf_report(report, patient_name)
                
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=pdf_file.read(),
                        file_name=f"{patient_name}_health_report.pdf",
                        mime="application/pdf"
                    )
                    
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
