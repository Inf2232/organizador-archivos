import os
import google.generativeai as genai
from dotenv import load_dotenv

def clasificar_por_ia(nombre_archivo):
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return ""

    # Configurar la API
    genai.configure(api_key=api_key)

    # Elegir el modelo gratuito
    modelo = genai.GenerativeModel("gemini-3.6-flash")

    prompt = f"Analiza el siguiente nombre de archivo: '{nombre_archivo}'. Determina su tema principal (ej: tecnología, música, educación, finanzas, marketing, legal, salud, deportes, entretenimiento, etc.). Responde únicamente con una palabra corta que represente el tema. Si el nombre no es descriptivo o no puedes deducirlo, responde exactamente 'ninguno'."

    try:
        respuesta = modelo.generate_content(prompt)
        tema = respuesta.text.strip().lower()
        if tema == "ninguno" or tema == "":
            return ""
        return tema
    except Exception as e:
        print(f"Error al llamar a Gemini: {e}")
        return ""