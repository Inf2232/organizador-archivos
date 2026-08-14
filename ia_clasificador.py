import os
from dotenv import load_dotenv
from google import genai
    

def clasificar_por_ia(nombre_archivo):
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return ""

    client = genai.Client(api_key=api_key)
    chat = client.chats.create(model="gemini-3.6-flash")

    prompt = f"Analiza el siguiente nombre de archivo: '{nombre_archivo}'. Determina su tema principal (ej: tecnología, música, educación, finanzas, marketing, legal, salud, deportes, entretenimiento, etc.). Responde únicamente con una palabra corta que represente el tema. Si el nombre no es descriptivo o no puedes deducirlo, responde exactamente 'ninguno'."

    try:
            response = chat.send_message(prompt)
            tema = response.text.strip().lower()
            if tema == "ninguno" or tema == "":
                return ""
            return tema
    except Exception as e:
            print(f"Error al llamar a Gemini: {e}")
            return ""