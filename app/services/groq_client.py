"""
Client Groq centralisé avec gestion automatique du rate limiting
Version finale - Novembre 2025
"""
import time
import google.generativeai as genai
from groq import Groq
from app.config import GEMINI_API_KEY, GROQ_API_KEY, AI_PROVIDER

# Configuration des clients
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

client_groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def call_gemini(prompt):
    """Appelle Gemini."""
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    response = model.generate_content(prompt)
    return response.text


def call_groq(prompt, max_retries=3):
    """
    Appelle Groq avec gestion automatique du rate limiting (429).
    
    Si rate limit atteint :
    - Attend le temps indiqué par l'API
    - Réessaye automatiquement (max 3 fois)
    
    Args:
        prompt: Le prompt à envoyer à Groq
        max_retries: Nombre maximum de tentatives (défaut: 3)
        
    Returns:
        La réponse de Groq en format texte
    """
    if not client_groq:
        raise ValueError("❌ La clé API Groq n'est pas configurée dans .env")
    
    for attempt in range(max_retries):
        try:
            chat_completion = client_groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            error_str = str(e)
            
            # Détecter le rate limit (429)
            if "rate_limit" in error_str.lower() or "429" in error_str:
                # Extraire le temps d'attente suggéré
                wait_time = 12  # Par défaut 12 secondes
                
                if "try again in" in error_str:
                    try:
                        # Extraire "try again in 10.44s"
                        parts = error_str.split("try again in ")[1].split("s")[0]
                        wait_time = float(parts) + 1  # +1 seconde de sécurité
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    print(f"    ⏳ Rate limit atteint, attente de {wait_time:.0f}s... (tentative {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"    ❌ Rate limit persistant après {max_retries} tentatives")
                    raise
            else:
                print(f"❌ Erreur Groq : {e}")
                raise