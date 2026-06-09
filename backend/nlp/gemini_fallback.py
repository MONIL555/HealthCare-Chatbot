import os
# pyrefly: ignore [missing-import]
import google.generativeai as genai
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class GeminiFallback:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. LLM fallback will not work.")
            self.model = None
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3.5-flash')

    def generate_response(self, query: str, user_profile: Optional[Dict] = None) -> str:
        """Generates a contextual response using Gemini API."""
        if not self.api_key or not self.model:
            return "I am unable to connect to my advanced language engine at the moment. Please try asking about specific symptoms, or contact an administrator to configure the GEMINI_API_KEY."

        context = ""
        if user_profile:
            age = user_profile.get('age') or 'Unknown'
            gender = user_profile.get('gender') or 'Unknown'
            conditions = user_profile.get('medical_conditions') or []
            allergies = user_profile.get('allergies') or []
            
            context = f"\nUser Context:\nAge: {age}\nGender: {gender}\n"
            if conditions:
                context += f"Pre-existing Conditions: {', '.join(conditions)}\n"
            if allergies:
                context += f"Allergies: {', '.join(allergies)}\n"

        prompt = (
            "You are HealthBot, a professional, empathetic AI Healthcare Assistant. "
            "Your goal is to provide general health advice, clarify medical terms, "
            "and offer support. \n"
            "CRITICAL RULES:\n"
            "1. DO NOT DIAGNOSE. If the user shares severe symptoms, gently advise them to consult a doctor or seek emergency care.\n"
            "2. Keep responses concise, clear, and empathetic. Use bullet points if helpful.\n"
            "3. Take the user's medical profile into account if provided.\n"
            f"{context}\n"
            f"User Query: {query}\n"
            "Response:"
        )

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "I'm having trouble processing your request right now. Please try again later."
