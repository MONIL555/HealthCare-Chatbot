"""
Symptom-based Disease Classifier

ML-based disease prediction using Decision Tree and SVM classifiers
trained on structured symptom CSV datasets. Includes NLP-based symptom
extraction from natural language queries.
"""

import os
import csv
import json
import pickle
import re
import numpy as np
import pandas as pd
from sklearn import preprocessing
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODEL_DIR = os.path.join(BASE_DIR, 'models')

# Dataset paths
TRAINING_CSV = os.path.join(DATA_DIR, 'Training.csv')
TESTING_CSV = os.path.join(DATA_DIR, 'Testing.csv')
SEVERITY_CSV = os.path.join(DATA_DIR, 'symptom_severity.csv')
DESCRIPTION_CSV = os.path.join(DATA_DIR, 'symptom_description.csv')
PRECAUTION_CSV = os.path.join(DATA_DIR, 'symptom_precaution.csv')

# Model paths
DT_MODEL_PATH = os.path.join(MODEL_DIR, 'decision_tree.pkl')
SVM_MODEL_PATH = os.path.join(MODEL_DIR, 'svm_model.pkl')
ENCODER_PATH = os.path.join(MODEL_DIR, 'label_encoder.pkl')
COLUMNS_PATH = os.path.join(MODEL_DIR, 'symptom_columns.pkl')

# ────────────────────────────────────────────────────────────
# Symptom synonyms for NLP extraction
# Maps natural language terms → dataset column names
# ────────────────────────────────────────────────────────────
SYMPTOM_SYNONYMS = {
    # Skin & Appearance
    "itching": ["itching", "itchy", "itch", "scratchy skin"],
    "skin_rash": ["skin rash", "rash", "rashes", "skin eruption", "red patches"],
    "nodal_skin_eruptions": ["nodal skin eruptions", "skin eruptions", "skin bumps", "nodal eruptions"],
    "continuous_sneezing": ["continuous sneezing", "sneezing", "sneeze", "constant sneezing", "keep sneezing"],
    "shivering": ["shivering", "shiver", "trembling", "shaking"],
    "chills": ["chills", "chill", "cold chills", "feeling cold"],
    "joint_pain": ["joint pain", "joints hurt", "aching joints", "painful joints", "arthritis pain"],
    "stomach_pain": ["stomach pain", "stomach ache", "tummy ache", "abdominal cramps", "belly ache", "stomach hurts"],
    "acidity": ["acidity", "acid reflux", "heartburn", "acidic", "sour stomach"],
    "ulcers_on_tongue": ["ulcers on tongue", "tongue ulcers", "mouth sores", "canker sores"],
    "muscle_wasting": ["muscle wasting", "muscle loss", "muscle atrophy", "losing muscle"],
    "vomiting": ["vomiting", "vomit", "throwing up", "puking", "nausea and vomiting"],
    "burning_micturition": ["burning micturition", "burning urination", "burning pee", "painful urination", "burns when i pee"],
    "spotting_urination": ["spotting urination", "spotting while urinating", "blood in urine"],
    "fatigue": ["fatigue", "tired", "exhausted", "feeling tired", "tiredness", "low energy", "no energy", "fatigued"],
    "weight_gain": ["weight gain", "gaining weight", "putting on weight", "getting fat"],
    "anxiety": ["anxiety", "anxious", "worried", "nervousness", "nervous", "panic", "stress"],
    "cold_hands_and_feets": ["cold hands and feet", "cold hands", "cold feet", "cold extremities", "hands and feet cold"],
    "mood_swings": ["mood swings", "mood changes", "emotional", "irritable mood"],
    "weight_loss": ["weight loss", "losing weight", "lost weight", "unintentional weight loss"],
    "restlessness": ["restlessness", "restless", "can't sit still", "agitated", "cant relax"],
    "lethargy": ["lethargy", "lethargic", "sluggish", "lazy", "no motivation"],
    "patches_in_throat": ["patches in throat", "throat patches", "white patches throat"],
    "irregular_sugar_level": ["irregular sugar level", "blood sugar fluctuation", "sugar level unstable", "sugar level irregular"],
    "cough": ["cough", "coughing", "dry cough", "wet cough", "persistent cough", "can't stop coughing"],
    "high_fever": ["high fever", "fever", "high temperature", "running a fever", "burning up", "feverish", "temperature"],
    "sunken_eyes": ["sunken eyes", "eyes sunken", "dark circles", "hollow eyes"],
    "breathlessness": ["breathlessness", "shortness of breath", "difficulty breathing", "can't breathe", "breathless", "hard to breathe", "breathing difficulty"],
    "sweating": ["sweating", "excessive sweating", "perspiring", "sweat a lot", "night sweats"],
    "dehydration": ["dehydration", "dehydrated", "not enough water", "dry mouth"],
    "indigestion": ["indigestion", "upset stomach", "dyspepsia", "can't digest", "digestion problem"],
    "headache": ["headache", "head hurts", "head pain", "migraine", "pounding head", "throbbing head", "head ache"],
    "yellowish_skin": ["yellowish skin", "yellow skin", "jaundice skin", "skin turning yellow"],
    "dark_urine": ["dark urine", "dark pee", "brown urine", "dark colored urine"],
    "nausea": ["nausea", "nauseous", "feel sick", "queasy", "feeling nauseous"],
    "loss_of_appetite": ["loss of appetite", "no appetite", "not hungry", "don't feel like eating", "appetite loss"],
    "pain_behind_the_eyes": ["pain behind eyes", "eye pain", "eyes hurt", "pain behind the eyes"],
    "back_pain": ["back pain", "backache", "lower back pain", "upper back pain", "back hurts", "spine pain"],
    "constipation": ["constipation", "constipated", "can't poop", "difficulty passing stool"],
    "abdominal_pain": ["abdominal pain", "stomach pain", "belly pain", "abdomen hurts", "lower abdomen pain"],
    "diarrhoea": ["diarrhea", "diarrhoea", "loose stools", "watery stool", "runny stomach", "loose motions"],
    "mild_fever": ["mild fever", "slight fever", "low grade fever", "low fever"],
    "yellow_urine": ["yellow urine", "dark yellow pee"],
    "yellowing_of_eyes": ["yellowing of eyes", "yellow eyes", "eyes turning yellow", "jaundice eyes"],
    "acute_liver_failure": ["liver failure", "acute liver failure"],
    "fluid_overload": ["fluid overload", "fluid retention", "water retention", "swelling"],
    "swelling_of_stomach": ["swelling of stomach", "bloated stomach", "stomach swelling", "bloating", "bloated"],
    "swelled_lymph_nodes": ["swollen lymph nodes", "swelled lymph nodes", "lymph node swelling", "swollen glands"],
    "malaise": ["malaise", "general discomfort", "unwell", "feeling unwell", "not feeling well"],
    "blurred_and_distorted_vision": ["blurred vision", "distorted vision", "blurry vision", "can't see clearly", "vision problems"],
    "phlegm": ["phlegm", "mucus", "sputum", "thick mucus"],
    "throat_irritation": ["throat irritation", "irritated throat", "scratchy throat", "tickle in throat", "sore throat", "throat hurts", "throat pain"],
    "redness_of_eyes": ["red eyes", "redness of eyes", "bloodshot eyes", "eye redness"],
    "sinus_pressure": ["sinus pressure", "sinus pain", "sinus congestion", "sinusitis"],
    "runny_nose": ["runny nose", "nose running", "nasal discharge", "runny"],
    "congestion": ["congestion", "nasal congestion", "blocked nose", "stuffy nose", "stuffed up"],
    "chest_pain": ["chest pain", "chest hurts", "chest tightness", "pain in chest"],
    "weakness_in_limbs": ["weakness in limbs", "weak arms", "weak legs", "limb weakness"],
    "fast_heart_rate": ["fast heart rate", "rapid heartbeat", "heart racing", "tachycardia", "heart pounding", "palpitations"],
    "pain_during_bowel_movements": ["pain during bowel movements", "painful bowel movement", "hurts to poop"],
    "pain_in_anal_region": ["pain in anal region", "anal pain", "rectal pain"],
    "bloody_stool": ["bloody stool", "blood in stool", "bleeding stool"],
    "irritation_in_anus": ["irritation in anus", "anal irritation", "itchy anus"],
    "neck_pain": ["neck pain", "stiff neck", "neck hurts", "neck ache"],
    "dizziness": ["dizziness", "dizzy", "lightheaded", "light headed", "vertigo", "feeling faint"],
    "cramps": ["cramps", "cramping", "muscle cramps", "leg cramps", "period cramps"],
    "bruising": ["bruising", "bruises", "easy bruising", "bruise easily"],
    "obesity": ["obesity", "overweight", "obese", "very heavy"],
    "swollen_legs": ["swollen legs", "leg swelling", "legs swollen", "puffy legs"],
    "swollen_blood_vessels": ["swollen blood vessels", "varicose veins", "visible veins"],
    "puffy_face_and_eyes": ["puffy face", "puffy eyes", "swollen face", "face swelling"],
    "enlarged_thyroid": ["enlarged thyroid", "goiter", "thyroid swelling", "thyroid enlarged"],
    "brittle_nails": ["brittle nails", "nails breaking", "weak nails", "fragile nails"],
    "swollen_extremeties": ["swollen extremities", "swollen hands", "swollen feet", "extremity swelling"],
    "excessive_hunger": ["excessive hunger", "always hungry", "hungry all the time", "increased hunger"],
    "extra_marital_contacts": ["extra marital contacts", "unprotected sex", "multiple partners"],
    "drying_and_tingling_lips": ["dry lips", "tingling lips", "drying lips", "lips tingling"],
    "slurred_speech": ["slurred speech", "speech difficulty", "trouble speaking", "can't speak properly"],
    "knee_pain": ["knee pain", "knee hurts", "painful knee", "knee ache"],
    "hip_joint_pain": ["hip pain", "hip joint pain", "hip hurts"],
    "muscle_weakness": ["muscle weakness", "weak muscles", "muscles weak", "muscular weakness"],
    "stiff_neck": ["stiff neck", "neck stiffness", "neck is stiff"],
    "swelling_joints": ["swelling joints", "joint swelling", "joints swollen", "swollen joints"],
    "movement_stiffness": ["movement stiffness", "stiff movement", "stiffness", "hard to move"],
    "spinning_movements": ["spinning movements", "spinning sensation", "room spinning", "everything spinning"],
    "loss_of_balance": ["loss of balance", "losing balance", "unsteady", "off balance"],
    "unsteadiness": ["unsteadiness", "unsteady", "wobbling", "can't walk straight"],
    "weakness_of_one_body_side": ["weakness of one body side", "one side weak", "one sided weakness", "hemiparesis"],
    "loss_of_smell": ["loss of smell", "can't smell", "anosmia", "no smell"],
    "bladder_discomfort": ["bladder discomfort", "bladder pain", "bladder pressure"],
    "foul_smell_of_urine": ["foul smell of urine", "smelly urine", "urine smells bad"],
    "continuous_feel_of_urine": ["continuous feel of urine", "urge to urinate", "frequent urination", "always need to pee"],
    "passage_of_gases": ["passage of gases", "gas", "flatulence", "passing gas", "bloated with gas"],
    "internal_itching": ["internal itching", "itching inside"],
    "toxic_look_(typhos)": ["toxic look", "typhos", "toxic appearance"],
    "depression": ["depression", "depressed", "feeling depressed", "sad", "hopeless"],
    "irritability": ["irritability", "irritable", "easily annoyed", "short tempered"],
    "muscle_pain": ["muscle pain", "myalgia", "muscles ache", "body pain", "body ache", "sore muscles", "muscle ache"],
    "altered_sensorium": ["altered sensorium", "confusion", "disoriented", "altered consciousness"],
    "red_spots_over_body": ["red spots", "red spots over body", "spots on body", "body spots"],
    "belly_pain": ["belly pain", "tummy pain", "stomach hurting"],
    "abnormal_menstruation": ["abnormal menstruation", "irregular periods", "period problems", "menstrual irregularity"],
    "dischromic_patches": ["dischromic patches", "skin discoloration", "patches on skin"],
    "watering_from_eyes": ["watering eyes", "eyes watering", "teary eyes", "watery eyes"],
    "increased_appetite": ["increased appetite", "eating more", "always eating"],
    "polyuria": ["polyuria", "frequent urination", "peeing a lot", "urinating frequently"],
    "family_history": ["family history", "runs in family", "genetic", "hereditary"],
    "mucoid_sputum": ["mucoid sputum", "mucus cough", "thick sputum"],
    "rusty_sputum": ["rusty sputum", "rust colored sputum", "brown sputum"],
    "lack_of_concentration": ["lack of concentration", "can't concentrate", "poor focus", "difficulty focusing"],
    "visual_disturbances": ["visual disturbances", "vision problems", "seeing spots", "visual issues"],
    "receiving_blood_transfusion": ["blood transfusion", "received blood"],
    "receiving_unsterile_injections": ["unsterile injections", "dirty needles"],
    "coma": ["coma", "unconscious", "unresponsive"],
    "stomach_bleeding": ["stomach bleeding", "internal bleeding", "blood vomit"],
    "distention_of_abdomen": ["distention of abdomen", "abdomen distended", "swollen abdomen"],
    "history_of_alcohol_consumption": ["alcohol consumption", "drinking alcohol", "heavy drinking", "alcoholic"],
    "blood_in_sputum": ["blood in sputum", "coughing blood", "bloody cough", "hemoptysis"],
    "prominent_veins_on_calf": ["prominent veins on calf", "visible calf veins", "varicose veins calf"],
    "palpitations": ["palpitations", "heart palpitations", "heart fluttering"],
    "painful_walking": ["painful walking", "pain while walking", "hurts to walk", "difficulty walking"],
    "pus_filled_pimples": ["pus filled pimples", "pimples with pus", "pustules", "acne"],
    "blackheads": ["blackheads", "black heads", "open comedones"],
    "scurring": ["scarring", "scurring", "skin scarring", "scars"],
    "skin_peeling": ["skin peeling", "peeling skin", "skin flaking"],
    "silver_like_dusting": ["silver like dusting", "silvery scales", "silver scales"],
    "small_dents_in_nails": ["small dents in nails", "nail pitting", "nail dents"],
    "inflammatory_nails": ["inflammatory nails", "nail inflammation", "inflamed nails"],
    "blister": ["blister", "blisters", "skin blisters", "water blisters"],
    "red_sore_around_nose": ["red sore around nose", "sore nose", "nose sore"],
    "yellow_crust_ooze": ["yellow crust ooze", "yellow crust", "oozing", "crusting"],
    # Additional fluid_overload variant (appears twice in dataset)
    "fluid_overload.1": ["fluid overload", "excess fluid"],
}


class SymptomClassifier:
    """ML-based disease prediction from symptoms."""

    def __init__(self):
        self.dt_model = None       # Decision Tree
        self.svm_model = None      # Support Vector Machine
        self.label_encoder = None
        self.symptom_columns = []
        self.severity_dict = {}
        self.description_dict = {}
        self.precaution_dict = {}
        self.is_loaded = False

    # ────────────────────────────────────────────────────────
    # TRAINING
    # ────────────────────────────────────────────────────────
    def train(self):
        """Train Decision Tree and SVM on Training.csv."""
        print("=" * 60)
        print("  TRAINING SYMPTOM CLASSIFIER")
        print("=" * 60)

        # Load training data
        training = pd.read_csv(TRAINING_CSV)
        testing = pd.read_csv(TESTING_CSV)

        self.symptom_columns = list(training.columns[:-1])  # All except 'prognosis'

        X = training[self.symptom_columns]
        y = training['prognosis']

        # Encode disease labels
        self.label_encoder = preprocessing.LabelEncoder()
        self.label_encoder.fit(y)
        y_encoded = self.label_encoder.transform(y)

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.33, random_state=42
        )

        # Prepare test data
        test_X = testing[self.symptom_columns]
        test_y = self.label_encoder.transform(testing['prognosis'])

        # ── Decision Tree ─────────────────────────────────
        print("\n[*] Training Decision Tree...")
        self.dt_model = DecisionTreeClassifier()
        self.dt_model.fit(X_train, y_train)

        dt_train_score = self.dt_model.score(X_train, y_train)
        dt_cv_scores = cross_val_score(self.dt_model, X_test, y_test, cv=3)
        dt_test_score = self.dt_model.score(test_X, test_y)

        print(f"   Train accuracy:  {dt_train_score:.4f}")
        print(f"   CV mean accuracy: {dt_cv_scores.mean():.4f}")
        print(f"   Test accuracy:   {dt_test_score:.4f}")

        # ── SVM ───────────────────────────────────────────
        print("\n[*] Training SVM...")
        self.svm_model = SVC(probability=True)
        self.svm_model.fit(X_train, y_train)

        svm_train_score = self.svm_model.score(X_train, y_train)
        svm_test_score = self.svm_model.score(test_X, test_y)

        print(f"   Train accuracy:  {svm_train_score:.4f}")
        print(f"   Test accuracy:   {svm_test_score:.4f}")

        # ── Save models ──────────────────────────────────
        os.makedirs(MODEL_DIR, exist_ok=True)

        with open(DT_MODEL_PATH, 'wb') as f:
            pickle.dump(self.dt_model, f)
        with open(SVM_MODEL_PATH, 'wb') as f:
            pickle.dump(self.svm_model, f)
        with open(ENCODER_PATH, 'wb') as f:
            pickle.dump(self.label_encoder, f)
        with open(COLUMNS_PATH, 'wb') as f:
            pickle.dump(self.symptom_columns, f)

        print(f"\n[OK] Models saved to {MODEL_DIR}")
        print(f"   Diseases covered: {len(self.label_encoder.classes_)}")
        print(f"   Symptom features: {len(self.symptom_columns)}")
        print("=" * 60)

        # Load supporting data
        self._load_severity()
        self._load_descriptions()
        self._load_precautions()
        self.is_loaded = True

        return {
            "dt_accuracy": float(dt_test_score),
            "svm_accuracy": float(svm_test_score),
            "diseases": len(self.label_encoder.classes_),
            "symptoms": len(self.symptom_columns),
        }

    # ────────────────────────────────────────────────────────
    # LOADING
    # ────────────────────────────────────────────────────────
    def load_models(self):
        """Load pre-trained models or train from scratch."""
        all_exist = all(os.path.exists(p) for p in [
            DT_MODEL_PATH, SVM_MODEL_PATH, ENCODER_PATH, COLUMNS_PATH
        ])

        if all_exist:
            print("Loading pre-trained symptom classifier...")
            with open(DT_MODEL_PATH, 'rb') as f:
                self.dt_model = pickle.load(f)
            with open(SVM_MODEL_PATH, 'rb') as f:
                self.svm_model = pickle.load(f)
            with open(ENCODER_PATH, 'rb') as f:
                self.label_encoder = pickle.load(f)
            with open(COLUMNS_PATH, 'rb') as f:
                self.symptom_columns = pickle.load(f)
            print(f"  Loaded {len(self.label_encoder.classes_)} diseases, {len(self.symptom_columns)} symptoms")
        else:
            print("No pre-trained models found. Training from scratch...")
            self.train()

        self._load_severity()
        self._load_descriptions()
        self._load_precautions()
        self.is_loaded = True

    def _load_severity(self):
        """Load symptom severity weights."""
        self.severity_dict = {}
        if os.path.exists(SEVERITY_CSV):
            try:
                with open(SEVERITY_CSV, encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            symptom = row[0].strip()
                            try:
                                weight = int(row[1].strip())
                            except ValueError:
                                continue
                            self.severity_dict[symptom] = weight
            except Exception as e:
                print(f"Warning: Could not load severity data: {e}")

    def _load_descriptions(self):
        """Load disease descriptions."""
        self.description_dict = {}
        if os.path.exists(DESCRIPTION_CSV):
            try:
                with open(DESCRIPTION_CSV, encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            self.description_dict[row[0].strip()] = row[1].strip()
            except Exception as e:
                print(f"Warning: Could not load description data: {e}")

    def _load_precautions(self):
        """Load disease precautions."""
        self.precaution_dict = {}
        if os.path.exists(PRECAUTION_CSV):
            try:
                with open(PRECAUTION_CSV, encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            disease = row[0].strip()
                            precautions = [p.strip() for p in row[1:] if p.strip()]
                            self.precaution_dict[disease] = precautions
            except Exception as e:
                print(f"Warning: Could not load precaution data: {e}")

    # ────────────────────────────────────────────────────────
    # SYMPTOM EXTRACTION (NLP)
    # ────────────────────────────────────────────────────────
    def extract_symptoms(self, query: str) -> list:
        """
        Extract symptom column names from a natural language query.
        Uses fuzzy keyword matching against SYMPTOM_SYNONYMS.
        """
        query_lower = query.lower().strip()
        # Clean punctuation for matching
        query_clean = re.sub(r'[^\w\s]', ' ', query_lower)
        query_clean = re.sub(r'\s+', ' ', query_clean).strip()

        matched_symptoms = set()

        for symptom_col, synonyms in SYMPTOM_SYNONYMS.items():
            for syn in synonyms:
                syn_lower = syn.lower()
                # Check if synonym appears in the query
                if syn_lower in query_clean:
                    # Verify it's a real column in our dataset
                    col_name = symptom_col.rstrip('.1')  # handle fluid_overload.1
                    if col_name in self.symptom_columns or symptom_col in self.symptom_columns:
                        matched_symptoms.add(col_name if col_name in self.symptom_columns else symptom_col)
                    break

        return list(matched_symptoms)

    def _build_symptom_vector(self, matched_symptoms: list) -> pd.DataFrame:
        """Convert matched symptom names into a binary feature DataFrame."""
        vector = np.zeros(len(self.symptom_columns), dtype=int)
        for symptom in matched_symptoms:
            if symptom in self.symptom_columns:
                idx = self.symptom_columns.index(symptom)
                vector[idx] = 1
        return pd.DataFrame([vector], columns=self.symptom_columns)

    # ────────────────────────────────────────────────────────
    # PREDICTION
    # ────────────────────────────────────────────────────────
    def predict(self, query: str) -> dict:
        """
        Full prediction pipeline:
        1. Extract symptoms from natural language
        2. Predict disease using DT + SVM
        3. Return rich response with description, precautions, severity
        """
        if not self.is_loaded:
            self.load_models()

        # Step 1: Extract symptoms
        matched_symptoms = self.extract_symptoms(query)

        if not matched_symptoms:
            return {
                "success": False,
                "matched_symptoms": [],
                "message": "No symptoms detected in query."
            }

        # Step 2: Build feature vector and predict
        symptom_vector = self._build_symptom_vector(matched_symptoms)

        dt_prediction = self.dt_model.predict(symptom_vector)[0]
        dt_disease = self.label_encoder.inverse_transform([dt_prediction])[0]

        svm_prediction = self.svm_model.predict(symptom_vector)[0]
        svm_disease = self.label_encoder.inverse_transform([svm_prediction])[0]

        # Get SVM probability for confidence
        svm_proba = self.svm_model.predict_proba(symptom_vector)
        svm_confidence = float(np.max(svm_proba))

        # Consensus check
        if dt_disease == svm_disease:
            final_disease = dt_disease
            confidence = max(svm_confidence, 0.85)  # High confidence when models agree
        else:
            # Use SVM as primary (generally better for this task)
            final_disease = svm_disease
            confidence = svm_confidence * 0.9  # Slightly lower when models disagree

        # Step 3: Gather rich response data
        description = self.description_dict.get(final_disease, "")
        precautions = self.precaution_dict.get(final_disease, [])

        # Calculate severity
        severity_score = self._calc_severity(matched_symptoms)
        urgency = self._get_urgency(severity_score, len(matched_symptoms))

        # Determine specialist recommendation
        specialist = self._get_specialist(final_disease)

        # Format human-readable symptom names
        readable_symptoms = [s.replace('_', ' ').title() for s in matched_symptoms]

        # Build the tailored response text
        response_text = self._build_response(
            final_disease, description, precautions,
            readable_symptoms, urgency, severity_score
        )

        # ── Follow-up for low confidence ──────────────────────
        follow_up_question = None
        if confidence < 0.60:
            follow_up_question = (
                "I'm not entirely confident with this assessment based on the few symptoms provided. "
                "Could you share more details, such as how long you've had these symptoms, "
                "or any other minor changes you've noticed in your body?"
            )
            # Append follow-up to the response
            response_text += f"\n\n**Note:** {follow_up_question}"

        return {
            "success": True,
            "disease": final_disease,
            "confidence": round(confidence, 4),
            "dt_prediction": dt_disease,
            "svm_prediction": svm_disease,
            "matched_symptoms": readable_symptoms,
            "matched_symptom_keys": matched_symptoms,
            "description": description,
            "precautions": precautions,
            "severity_score": severity_score,
            "urgency": urgency,
            "specialist": specialist,
            "response": response_text,
            "follow_up_question": follow_up_question
        }

    def _calc_severity(self, symptoms: list, days: int = 1) -> int:
        """Calculate severity score from matched symptoms."""
        total = 0
        for s in symptoms:
            total += self.severity_dict.get(s, 3)  # Default weight 3
        return total

    def _get_urgency(self, severity_score: int, num_symptoms: int) -> str:
        """Determine urgency level from severity score."""
        if num_symptoms == 0:
            return "low"

        avg_severity = severity_score / max(num_symptoms, 1)

        if avg_severity >= 6 or severity_score >= 25:
            return "emergency"
        elif avg_severity >= 5 or severity_score >= 18:
            return "high"
        elif avg_severity >= 3.5 or severity_score >= 10:
            return "medium"
        else:
            return "low"

    def _get_specialist(self, disease: str) -> str:
        """Recommend a specialist based on predicted disease."""
        specialist_map = {
            "Fungal infection": "Dermatologist",
            "Allergy": "Allergist / Immunologist",
            "GERD": "Gastroenterologist",
            "Chronic cholestasis": "Hepatologist",
            "Drug Reaction": "Allergist / Emergency Medicine",
            "Peptic ulcer diseae": "Gastroenterologist",
            "AIDS": "Infectious Disease Specialist",
            "Diabetes ": "Endocrinologist",
            "Diabetes": "Endocrinologist",
            "Gastroenteritis": "Gastroenterologist",
            "Bronchial Asthma": "Pulmonologist",
            "Hypertension ": "Cardiologist",
            "Hypertension": "Cardiologist",
            "Migraine": "Neurologist",
            "Cervical spondylosis": "Orthopedic Specialist",
            "Paralysis (brain hemorrhage)": "Neurologist / Emergency Medicine",
            "Jaundice": "Hepatologist",
            "Malaria": "Infectious Disease Specialist",
            "Chicken pox": "General Physician",
            "Dengue": "Infectious Disease Specialist",
            "Typhoid": "Infectious Disease Specialist",
            "hepatitis A": "Hepatologist",
            "Hepatitis B": "Hepatologist",
            "Hepatitis C": "Hepatologist",
            "Hepatitis D": "Hepatologist",
            "Hepatitis E": "Hepatologist",
            "Alcoholic hepatitis": "Hepatologist",
            "Tuberculosis": "Pulmonologist",
            "Common Cold": "General Physician",
            "Pneumonia": "Pulmonologist",
            "Dimorphic hemmorhoids(piles)": "Proctologist",
            "Heart attack": "Cardiologist / Emergency Medicine",
            "Varicose veins": "Vascular Surgeon",
            "Hypothyroidism": "Endocrinologist",
            "Hyperthyroidism": "Endocrinologist",
            "Hypoglycemia": "Endocrinologist",
            "Osteoarthristis": "Orthopedic Specialist",
            "Arthritis": "Rheumatologist",
            "(vertigo) Paroymsal  Positional Vertigo": "ENT Specialist",
            "Acne": "Dermatologist",
            "Urinary tract infection": "Urologist",
            "Psoriasis": "Dermatologist",
            "Impetigo": "Dermatologist",
        }
        return specialist_map.get(disease, "General Physician")

    def _build_response(self, disease, description, precautions,
                        readable_symptoms, urgency, severity_score):
        """Build a human-readable tailored response."""
        # Opening
        symptom_list = ", ".join(readable_symptoms[:5])
        if len(readable_symptoms) > 5:
            symptom_list += f" and {len(readable_symptoms) - 5} more"

        response = f"Based on your symptoms ({symptom_list}), "

        if urgency == "emergency":
            response += f"this could indicate **{disease}** which requires immediate medical attention. "
        elif urgency == "high":
            response += f"you may be experiencing **{disease}**. Please consult a doctor soon. "
        else:
            response += f"you may be experiencing **{disease}**. "

        # Description
        if description:
            response += f"\n\n{description}"

        # Precautions
        if precautions:
            response += "\n\n**Recommended precautions:**\n"
            for i, p in enumerate(precautions, 1):
                response += f"{i}. {p.capitalize()}\n"

        # Severity note
        if urgency in ("high", "emergency"):
            response += "\nNote: Given the severity of your symptoms, please seek professional medical advice promptly."
        else:
            response += "\nIf symptoms persist or worsen, please consult a healthcare professional."

        return response.strip()


if __name__ == "__main__":
    classifier = SymptomClassifier()
    classifier.train()

    # Test predictions
    test_queries = [
        "I have itching and skin rash",
        "high fever with chills and sweating",
        "I'm experiencing chest pain and breathlessness",
        "headache",
        "I have stomach pain, vomiting, and diarrhea",
        "I feel tired and have muscle pain with high fever",
    ]

    print("\n" + "=" * 60)
    print("  TEST PREDICTIONS")
    print("=" * 60)

    for query in test_queries:
        result = classifier.predict(query)
        if result["success"]:
            print(f"\nQuery: \"{query}\"")
            print(f"   Disease:    {result['disease']}")
            print(f"   Confidence: {result['confidence']:.1%}")
            print(f"   Symptoms:   {result['matched_symptoms']}")
            print(f"   Urgency:    {result['urgency']}")
            print(f"   Specialist: {result['specialist']}")
        else:
            print(f"\nQuery: \"{query}\" -> No symptoms detected")
