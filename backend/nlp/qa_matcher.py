import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, 'data', 'qa_dataset.json')
MODEL_DIR = os.path.join(BASE_DIR, 'models')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'qa_vectorizer.pkl')
MATRIX_PATH = os.path.join(MODEL_DIR, 'qa_matrix.pkl')

class QAMatcher:
    def __init__(self):
        self.vectorizer = None
        self.tfidf_matrix = None
        self.dataset = []
        
    def load_dataset(self):
        if not os.path.exists(DATASET_PATH):
            raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")
            
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            self.dataset = json.load(f)
            
    def train(self):
        print("Loading dataset...")
        self.load_dataset()
        
        questions = [item["question"] for item in self.dataset]
        
        print("Training TF-IDF Vectorizer on questions...")
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(questions)
        
        if not os.path.exists(MODEL_DIR):
            os.makedirs(MODEL_DIR)
            
        print("Saving vectorizer and matrix...")
        with open(VECTORIZER_PATH, 'wb') as f:
            pickle.dump(self.vectorizer, f)
            
        with open(MATRIX_PATH, 'wb') as f:
            pickle.dump(self.tfidf_matrix, f)
            
        print("Training complete!")

    def load_models(self):
        self.load_dataset()
        
        if os.path.exists(VECTORIZER_PATH) and os.path.exists(MATRIX_PATH):
            with open(VECTORIZER_PATH, 'rb') as f:
                self.vectorizer = pickle.load(f)
            with open(MATRIX_PATH, 'rb') as f:
                self.tfidf_matrix = pickle.load(f)
        else:
            print("Models not found. Training from scratch...")
            self.train()

    def transform_output(self, query: str, answer: str, base_problem: str) -> str:
        original_query = query
        query_lower = query.lower().strip()
        
        # ELIZA-style reflection for dynamic output on every single pair
        # Replace first-person pronouns with second-person
        reflected = re.sub(r'\bi\b', 'you', query_lower)
        reflected = re.sub(r'\bmy\b', 'your', reflected)
        reflected = re.sub(r'\bam\b', 'are', reflected)
        reflected = re.sub(r'\bme\b', 'you', reflected)
        reflected = re.sub(r'\bwe\b', 'you', reflected)
        reflected = re.sub(r'\bour\b', 'your', reflected)
        
        # Clean up punctuation at the end
        reflected = re.sub(r'[?.!]+$', '', reflected).strip()
        
        prefix = ""
        # Create a dynamic prefix based on the reflected query
        if len(reflected) > 0 and len(reflected) < 60:
            import random
            intros = [
                f"I understand that {reflected}.",
                f"It sounds like {reflected}.",
                f"I hear that {reflected}.",
                f"I see you are dealing with {reflected}." if not reflected.startswith("you") else f"I see {reflected}."
            ]
            prefix = random.choice(intros) + " "

        # Extract temperature (Specific Override Rule)
        temp_match = re.search(r'\b(9\d|10\d|11\d|12\d)(\.\d)?\b', query_lower)
        if temp_match and ('fever' in query_lower or 'temperature' in query_lower or 'high fever' in base_problem.lower()):
            temp = float(temp_match.group(0))
            if temp >= 104:
                return f"⚠️ URGENT: You mentioned a fever of {temp}°F. A temperature this high is a critical medical emergency! Please go to the nearest emergency room or call for an ambulance immediately."
            elif temp > 99:
                prefix = f"I see you have a fever of {temp}°F. "
                
        # Extract duration (e.g. '3 days')
        dur_match = re.search(r'\b(\d+)\s+(day|days|week|weeks|month|months)\b', query_lower)
        if dur_match and not temp_match:
            duration = dur_match.group(0)
            prefix = f"I understand you've been experiencing this for {duration}. "

        # Combine dynamic prefix with the dataset answer
        return f"{prefix}{answer}".strip()

    def match(self, query: str):
        if self.vectorizer is None or self.tfidf_matrix is None:
            self.load_models()
            
        # Vectorize user query
        query_vec = self.vectorizer.transform([query])
        
        # Compute similarities
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Get best match
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        if best_score > 0.1:  # Threshold
            best_match = self.dataset[best_idx]
            
            # Determine base problem implicitly from the match question if available
            base_problem = best_match.get("base_problem", best_match.get("question", ""))
            
            # Pick a random answer variation
            answers = best_match.get("answers", [])
            if not answers:
                answers = [best_match.get("answer", "I don't have an answer for that.")]
            selected_answer = random.choice(answers)
            
            # Dynamically transform the output
            transformed_answer = self.transform_output(query, selected_answer, base_problem)
            
            return {
                "answer": transformed_answer,
                "matched_question": best_match["question"],
                "confidence": float(best_score),
                "base_problem": base_problem
            }
        else:
            return {
                "answer": "I'm sorry, I couldn't find a specific answer for your query. Please consult a healthcare professional for guidance.",
                "matched_question": None,
                "confidence": 0.0,
                "base_problem": "general"
            }

if __name__ == "__main__":
    matcher = QAMatcher()
    matcher.train()
    
    # Test
    res = matcher.match("I have a really bad headache")
    print(res)
