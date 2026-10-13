"""
test_gemini.py - Test rapide de la connexion à l'API Gemini
Usage: python test_gemini.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"🔑 Clé API chargée : {api_key[:12]}...{api_key[-4:]}")

import google.generativeai as genai

genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    model_name=os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
    generation_config={"temperature": 0.1, "max_output_tokens": 200}
)

print("⏳ Test de connexion à Gemini...")
response = model.generate_content(
    "Cite 3 marques automobiles historiques et leur année de fondation. Réponse courte."
)
print("\n✅ Connexion réussie ! Réponse de Gemini :")
print(response.text)
print("\n🚀 L'agent est prêt à collecter les données automobiles !")
