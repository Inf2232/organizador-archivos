# 📁 Organizador de Archivos Inteligente

¡Hola! 👋 Este es mi proyecto de organizador de archivos, el cual desarrollé para aprender Python, interfaces gráficas y un poco de inteligencia artificial. La idea surgió porque siempre tenía el escritorio lleno de archivos desordenados y quería automatizar la tarea de clasificarlos.

Lo que comenzó como un simple script para mover archivos por extensión se convirtió en una aplicación con interfaz gráfica, detección de duplicados, modo simulación, función deshacer y hasta clasificación por temas usando IA (Google Gemini). Fue un viaje increíble de aprendizaje y quiero compartirlo contigo.

---

## ✨ ¿Qué hace?

- **Clasifica automáticamente** tus archivos en carpetas según su tipo (imágenes, documentos, música, videos, subtítulos, etc.).
- **Modo simulación**: te muestra qué haría sin mover nada, ideal para probar sin miedo.
- **Función deshacer**: si te arrepientes, puedes revertir la última organización.
- **Detección de duplicados**: compara el contenido de los archivos (hash MD5) y te pregunta si quieres moverlos a una carpeta "Duplicados" o eliminarlos (los envía a la papelera).
- **Clasificación por IA (opcional)**: analiza el nombre del archivo y crea subcarpetas temáticas. Por ejemplo, `tutorial_python.mp4` iría a `Videos/Tecnología`.
- **Barra de progreso** para que veas el avance en tiempo real.
- **No se congela**: usa hilos para que la interfaz siga fluida incluso moviendo archivos pesados o consultando la IA.
- **Evita sobrescribir**: si ya existe un archivo con el mismo nombre, le agrega un número (ej. `foto_1.jpg`).

---

## 🛠️ Tecnologías que usé

- **Python 3.11 como lenguaje principal.
- **Tkinter** para la interfaz gráfica (viene con Python).
- **Google Gemini API** para la clasificación por IA (tiene capa gratuita).
- **Hashlib** para calcular hashes MD5 en duplicados.
- **Send2Trash** para eliminar archivos de forma segura (papelera).
- **Threading y Queue** para que la aplicación no se bloquee.

---

## 📷 Capturas

![Pantalla principal](<Captura de pantalla 2026-08-14 114630.png>)

---

## 🚀 Cómo usarlo

### Requisitos

- Python 3.8 o superior.
- Conexión a internet (solo si vas a usar la IA).
- Una API key gratuita de Google Gemini (opcional, para subcategorías).

### Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/TU_USUARIO/organizador-archivos.git
   cd organizador-archivos
2. Crea y activa un entorno virtual:
    python -m venv venv
    source venv/bin/activate      # En Windows: venv\Scripts\activate
3. Instala las dependencias:
    pip install -r requirements.
    
4. Configura la API (si quieres usar IA)

    Ve a Google AI Studio y crea tu clave gratuita.

    Crea un archivo .env en la raíz con:

    GEMINI_API_KEY=tu_clave_aquí

    Asegúrate de que .env esté en tu .gitignore para que no se suba a GitHub.

    Ejecuta
    bash

    python organizador_archivos.py

    Luego:

        Elige una carpeta con el botón "Seleccionar carpeta y organizar".

        Marca "Modo simulación" si quieres ver qué haría sin cambios reales.

        Marca "Usar IA para subcategorías" para crear subcarpetas temáticas (requiere API key).

        Si hay duplicados, te preguntará qué hacer.

        Puedes deshacer la última organización con el botón "Deshacer".


# 📁 Estructura del proyecto 
organizador-archivos/
── organizador_archivos.py   # Código principal (lógica + interfaz)
── categorias.py             # Diccionario con cientos de extensiones
── ia_clasificador.py        # Función para clasificar con Gemini
── .env.example              # Plantilla para tu API key
── .gitignore                # Ignora .env, __pycache__, etc.
── requirements.txt
── README.md