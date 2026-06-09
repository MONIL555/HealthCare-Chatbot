"""
Train the Symptom Classifier models.

Run this script to train/retrain the Decision Tree and SVM models
using the CSV datasets in backend/data/.

Usage:
    python train_model.py
"""

import sys
import os

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nlp.symptom_classifier import SymptomClassifier


def main():
    classifier = SymptomClassifier()
    result = classifier.train()

    print("\n" + "=" * 60)
    print("  TRAINING SUMMARY")
    print("=" * 60)
    print(f"  Decision Tree Accuracy: {result['dt_accuracy']:.2%}")
    print(f"  SVM Accuracy:           {result['svm_accuracy']:.2%}")
    print(f"  Diseases Covered:       {result['diseases']}")
    print(f"  Symptom Features:       {result['symptoms']}")
    print("=" * 60)

    # Run test predictions
    print("\nRunning test predictions...\n")

    test_queries = [
        "I have itching and skin rash",
        "high fever with chills and sweating",
        "I'm experiencing chest pain and breathlessness",
        "headache and nausea",
        "I have stomach pain, vomiting, and diarrhea",
        "I feel tired and have muscle pain with high fever",
        "I have a cough and sore throat",
        "burning urination and bladder discomfort",
    ]

    for query in test_queries:
        result = classifier.predict(query)
        if result["success"]:
            print(f"  [OK] \"{query}\"")
            print(f"     -> {result['disease']} ({result['confidence']:.0%} confidence)")
            print(f"       Symptoms: {', '.join(result['matched_symptoms'])}")
            print(f"       Urgency: {result['urgency']}")
            print()
        else:
            print(f"  [--] \"{query}\" -> No symptoms detected\n")

    print("Training complete! Restart the backend server to use the new models.")


if __name__ == "__main__":
    main()
