"""
Text preprocessing for medical queries.

Handles: text cleaning, tokenization, lemmatization, stop word removal,
and medical entity extraction using spaCy.
"""

import re
from typing import List, Dict

try:
    import spacy
    _SPACY_AVAILABLE = True
except ImportError:
    _SPACY_AVAILABLE = False

try:
    import nltk
    from nltk.corpus import stopwords
    # Download required NLTK data (silent)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
    _NLTK_AVAILABLE = True
except ImportError:
    _NLTK_AVAILABLE = False


class TextPreprocessor:
    """Text preprocessing pipeline for medical queries."""

    def __init__(self):
        # Load spaCy model
        self.nlp = None
        if _SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load('en_core_web_sm')
            except OSError:
                pass  # Model not downloaded; preprocess will use fallback

        # Stop words
        if _NLTK_AVAILABLE:
            self.stop_words = set(stopwords.words('english'))
        else:
            # Minimal fallback stop words
            self.stop_words = {
                'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'she',
                'it', 'they', 'the', 'a', 'an', 'is', 'are', 'was', 'were',
                'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
                'did', 'will', 'would', 'could', 'should', 'may', 'might',
                'shall', 'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at',
                'by', 'from', 'as', 'into', 'through', 'during', 'before',
                'after', 'above', 'below', 'between', 'and', 'but', 'or',
                'not', 'no', 'nor', 'so', 'very', 'just', 'than', 'too',
                'this', 'that', 'these', 'those', 'am', 'if', 'then',
            }

        # Medical terms to preserve (never remove as stop words)
        self.medical_terms = {
            'pain', 'ache', 'symptom', 'disease', 'medication', 'drug',
            'treatment', 'health', 'medical', 'sick', 'fever', 'cough',
            'cold', 'flu', 'infection', 'allergy', 'chronic', 'acute',
            'swelling', 'bleeding', 'nausea', 'fatigue', 'rash', 'itch',
            'burn', 'fracture', 'sprain', 'diabetes', 'asthma', 'cancer',
            'heart', 'lung', 'liver', 'kidney', 'brain', 'bone', 'joint',
            'muscle', 'skin', 'blood', 'pressure', 'sugar', 'weight',
            'pregnant', 'pregnancy', 'period', 'menstrual', 'vaccine',
            'screening', 'prevention', 'emergency', 'urgent', 'dosage',
            'pill', 'tablet', 'injection', 'surgery', 'diagnosis',
            'breathing', 'chest', 'head', 'stomach', 'back', 'neck',
            'shoulder', 'knee', 'ankle', 'wrist', 'hip', 'elbow',
        }

    def clean_text(self, text: str) -> str:
        """Basic text cleaning — lowercase, remove special chars, normalize whitespace."""
        text = text.lower()
        # Remove special characters except hyphens and periods (medical terms use them)
        text = re.sub(r'[^a-z0-9\s\-\.]', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text using spaCy (fallback: simple split)."""
        if self.nlp:
            doc = self.nlp(text)
            return [token.text for token in doc]
        return text.split()

    def lemmatize(self, text: str) -> str:
        """Lemmatize text using spaCy (fallback: return as-is)."""
        if self.nlp:
            doc = self.nlp(text)
            return ' '.join([token.lemma_ for token in doc])
        return text

    def remove_stopwords(self, text: str) -> str:
        """Remove stop words but preserve medical terms."""
        tokens = text.split()
        filtered = [
            token for token in tokens
            if token not in self.stop_words or token in self.medical_terms
        ]
        return ' '.join(filtered)

    def preprocess(self, text: str) -> str:
        """Complete preprocessing pipeline."""
        text = self.clean_text(text)
        text = self.lemmatize(text)
        text = self.remove_stopwords(text)
        return text

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract medical entities from text."""
        entities = {
            'symptoms': [],
            'medications': [],
            'body_parts': [],
            'conditions': []
        }

        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                # Map spaCy entity types to our categories
                if ent.label_ in ('DISEASE', 'CONDITION'):
                    entities['conditions'].append(ent.text)
                elif ent.label_ in ('CHEMICAL', 'DRUG'):
                    entities['medications'].append(ent.text)
                elif ent.label_ == 'ORG':
                    pass  # Skip organizations
                else:
                    # For general NER, use keyword matching as fallback
                    pass

        # Keyword-based entity extraction (supplements NER)
        text_lower = text.lower()

        body_parts_keywords = [
            'head', 'chest', 'back', 'neck', 'shoulder', 'arm', 'hand',
            'leg', 'foot', 'knee', 'ankle', 'wrist', 'hip', 'elbow',
            'stomach', 'abdomen', 'throat', 'ear', 'eye', 'nose',
            'skin', 'heart', 'lung', 'liver', 'kidney', 'brain',
        ]
        for part in body_parts_keywords:
            if part in text_lower:
                entities['body_parts'].append(part)

        symptom_keywords = [
            'pain', 'ache', 'fever', 'cough', 'nausea', 'vomiting',
            'dizziness', 'fatigue', 'weakness', 'swelling', 'bleeding',
            'rash', 'itching', 'burning', 'numbness', 'tingling',
            'shortness of breath', 'difficulty breathing',
        ]
        for symptom in symptom_keywords:
            if symptom in text_lower:
                entities['symptoms'].append(symptom)

        return entities
