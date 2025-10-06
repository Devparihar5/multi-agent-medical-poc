import streamlit as st

class Config:
    # Model Configuration
    MODEL_NAME = "models/gemini-2.0-flash-exp"
    TEMPERATURE = 0.3
    
    # API Keys
    @staticmethod
    def get_gemini_api_key():
        try:
            return st.secrets["api_keys"]["GEMINI_API_KEY"]
        except KeyError:
            raise ValueError("Gemini API key not found in secrets.toml")
    
    # Report Configuration
    MAX_SEARCH_RESULTS = 2
    MAX_SEARCH_TERMS = 2
