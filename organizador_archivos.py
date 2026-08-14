import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from pathlib import Path
from categorias import categorias  # Asegúrate de tener este archivo o pega aquí tu diccionario
import hashlib
from send2trash import send2trash

#Varibles Globales
ultimo_movimiento = []   # Almacenará los movimientos de la última organización real

# ---------- FUNCIONES DE LÓGICA ----------

def listar_archivos(ruta):
    """Devuelve una lista con los Path de todos los archivos en la carpeta."""
    archivos = []
    for archivo in ruta.iterdir():
        if archivo.is_file():
            archivos.append(archivo)
    return archivos


def clasificar_archivo(archivo):
    """Clasifica un archivo según su extensión usando el diccionario importado."""
    extension = archivo.suffix.lower()
    return categorias.get(extension, "Otros")


def obtener_destino_unico(destino):
    """
    Devuelve un Path de destino que no existe.
    Si 'destino' ya existe, agrega un número antes de la extensión.
    Ejemplo: documento.pdf -> documento_1.pdf -> documento_2.pdf ...
    """
    if not destino.exists():
        return destino

    contador = 1
    while True:
        nuevo = destino.with_name(f"{destino.stem}_{contador}{destino.suffix}")
        if not nuevo.exists():
            return nuevo
        contador += 1
def listar_archivos_recursivo(ruta):
    archivos = []
    for elemento in ruta.rglob('*'):
        if elemento.is_file():
            archivos.append(elemento)
    return archivos
def detectar_duplicados(ruta):
    """
    Devuelve una lista de grupos de archivos duplicados.
    Optimización: primero agrupa por tamaño y solo calcula hash si hay coincidencia.
    """
    archivos = listar_archivos_recursivo(ruta)
    por_tamano = {}

    # 1. Agrupar por tamaño
    for archivo in archivos:
        try:
            tam = archivo.stat().st_size
            por_tamano.setdefault(tam, []).append(archivo)
        except Exception as e:
            print(f"No se pudo obtener tamaño de {archivo.name}: {e}")

    grupos_finales = []

    # 2. Para cada grupo con más de un archivo, calcular hash
    for tam, lista_archivos in por_tamano.items():
        if len(lista_archivos) < 2:
            continue

        grupos_hash = {}
        for archivo in lista_archivos:
            try:
                contenido = archivo.read_bytes()
                hash_archivo = hashlib.md5(contenido).hexdigest()
                grupos_hash.setdefault(hash_archivo, []).append(archivo)
            except Exception as e:
                print(f"No se pudo leer {archivo.name}: {e}")

        # 3. Agregar solo los que realmente tienen duplicados
        for lista_dup in grupos_hash.values():
            if len(lista_dup) > 1:
                grupos_finales.append(lista_dup)

    return grupos_finales

def organizar_archivos(ruta, simulacion=False, registro=None, progreso=None):
    """
    Organiza todos los archivos de la carpeta 'ruta' en subcarpetas según su categoría.
    Parámetros:
        - ruta: Path de la carpeta a organizar.
        - simulacion: si True, solo muestra qué haría sin ejecutar.
        - registro: función callback que recibe un string (mensaje) para mostrar.
    Devuelve (movidos, errores).
    """
    archivos = listar_archivos(ruta)
    movidos = 0
    errores = []
    movimientos = [] # Lista para guardar (origen, destino) de cada archivo movido

    # Nombre del script actual para no moverse a sí mismo
    script_actual = Path(__file__).name

    def log(mensaje):
        """Envía el mensaje a la consola o a la función de registro si existe."""
        if registro:
            registro(mensaje)
        else:
            print(mensaje)

    for archivo in archivos:
        total_archivos = sum(1 for a in archivos if a.name != script_actual)
        procesados = 0
        if archivo.name == script_actual:
            continue
        procesados += 1
        if progreso:
            progreso(procesados / total_archivos if total_archivos > 0 else 1)

        try:

            categoria = clasificar_archivo(archivo)
            carpeta_destino = ruta / categoria

            # Calcular destino siempre (para simulación también)
            destino_inicial = carpeta_destino / archivo.name
            destino_final = obtener_destino_unico(destino_inicial)

            if simulacion:
                log(f"[Simulación] Crearía carpeta: {carpeta_destino.name}")
                log(f"[Simulación] Movería {archivo.name} → {carpeta_destino.name}/{destino_final.name}")
            else:
                carpeta_destino.mkdir(exist_ok=True)
                archivo.rename(destino_final)
                log(f"Movido: {archivo.name} → {carpeta_destino.name}/{destino_final.name}")
                movidos += 1
                movimientos.append((archivo, destino_final))    

        except Exception as e:
            errores.append((archivo.name, str(e)))
            log(f"Error al procesar {archivo.name}: {e}")

    if progreso:
        progreso(1.0)
    return movidos, errores,movimientos   

def mover_duplicados_a_carpeta(ruta, grupos_duplicados):
    carpeta_duplicados = ruta / "Duplicados"
    carpeta_duplicados.mkdir(exist_ok=True)
    movidos = 0
    movimientos_realizados = []  # Lista para guardar (origen, destino)

    for grupo in grupos_duplicados:
        for archivo in grupo[1:]:
            destino = carpeta_duplicados / archivo.name
            destino_final = obtener_destino_unico(destino)
            try:
                archivo.rename(destino_final)
                log_a_interfaz(f"🔁 Movido duplicado: {archivo.name} → Duplicados/{destino_final.name}")
                movidos += 1
                movimientos_realizados.append((archivo, destino_final))
            except Exception as e:
                log_a_interfaz(f"❌ Error al mover {archivo.name}: {e}")

    return movidos, movimientos_realizados   # Ahora devolvemos ambas cosas
def eliminar_duplicados(grupos_duplicados):
    eliminados = 0
    for grupo in grupos_duplicados:
        for archivo in grupo[1:]:
            try:
                send2trash(str(archivo))   # Envía a papelera
                log_a_interfaz(f"🗑️ Eliminado (papelera): {archivo.name}")
                eliminados += 1
            except Exception as e:
                log_a_interfaz(f"❌ Error al eliminar {archivo.name}: {e}")
    return eliminados

# ---------- FUNCIONES DE LA INTERFAZ ----------
def deshacer_ultima_organizacion():
    global ultimo_movimiento
    if not ultimo_movimiento:
        messagebox.showinfo("Deshacer", "No hay movimientos para deshacer.")
        return
    barra_progreso["value"] = 0
    area_texto.delete(1.0, tk.END)
    log_a_interfaz("🔄 Iniciando deshacer...")

    for origen, destino in reversed(ultimo_movimiento):
        try:
            # Verificar que el archivo destino aún exista
            if destino.exists():
                destino.rename(origen)
                log_a_interfaz(f"↩️ Revertido: {destino.name} → {origen.parent.name}/")
                # Intentar eliminar carpeta si quedó vacía (opcional)
                # carpeta = destino.parent
                # if carpeta.exists() and not any(carpeta.iterdir()):
                #     carpeta.rmdir()
                #     log_a_interfaz(f"🗑️ Carpeta vacía eliminada: {carpeta.name}")
            else:
                log_a_interfaz(f"⚠️ No se encontró {destino.name}, no se pudo revertir.")
        except Exception as e:
            log_a_interfaz(f"❌ Error al revertir {destino.name}: {e}")

    ultimo_movimiento = []  # Limpiar historial
    boton_deshacer.config(state="disabled")
    messagebox.showinfo("Deshacer", "Operación de deshacer completada.")
def log_a_interfaz(mensaje):
    """Inserta un mensaje en el área de texto de la interfaz."""
    area_texto.insert(tk.END, mensaje + "\n")
    area_texto.see(tk.END)  # Auto-scroll al final
def actualizar_progreso(valor):
    """Actualiza la barra de progreso (valor entre 0 y 1)."""
    barra_progreso["value"] = valor * 100
    root.update_idletasks()   # Refresca la interfaz

def seleccionar_carpeta_y_organizar():
    """Callback del botón: pide carpeta, ejecuta organización (real o simulada) y muestra resultado."""
    global ultimo_movimiento

    accion_duplicados = None          # "movidos", "eliminados" o None
    cantidad_duplicados = 0

    carpeta = filedialog.askdirectory()
    if not carpeta:
        return

    # Limpiar área de texto
    area_texto.delete(1.0, tk.END)

    # Actualizar etiqueta de carpeta
    etiqueta_carpeta.config(text=f"📂 {carpeta}")

    # Obtener modo simulación
    es_simulacion = modo_simulacion.get()

    # Ejecutar organizador con callback de log
    barra_progreso["value"] = 0
    movidos, errores, movimientos = organizar_archivos(
        Path(carpeta),
        simulacion=es_simulacion,
        registro=log_a_interfaz,
        progreso=actualizar_progreso 
    )

    if not es_simulacion:
        # Guardar historial inicial de movimientos (organización)
        ultimo_movimiento = movimientos
        boton_deshacer.config(state="normal")

        # Detectar duplicados después de organizar
        grupos_duplicados = detectar_duplicados(Path(carpeta))
        if grupos_duplicados:
            respuesta = messagebox.askyesno(
                "Duplicados encontrados",
                f"Se encontraron {len(grupos_duplicados)} grupos de archivos duplicados.\n"
                "¿Desea mover los duplicados a la carpeta 'Duplicados'?\n"
                "Seleccione 'No' para eliminarlos."
            )

            if respuesta:
                # Mover duplicados y obtener info
                movidos_duplicados, movimientos_dup = mover_duplicados_a_carpeta(
                    Path(carpeta), grupos_duplicados
                )
                cantidad_duplicados = movidos_duplicados
                accion_duplicados = "movidos"

                # Integrar movimientos de duplicados al historial de deshacer
                if movimientos_dup:
                    ultimo_movimiento = movimientos + movimientos_dup
                    boton_deshacer.config(state="normal")

            else:
                # Confirmación extra para eliminar
                confirmar = messagebox.askyesno(
                    "Confirmar eliminación",
                    "¿Está seguro de que desea ELIMINAR los archivos duplicados?\n"
                    "Los archivos se enviarán a la papelera."
                )
                if confirmar:
                    eliminados = eliminar_duplicados(grupos_duplicados)
                    cantidad_duplicados = eliminados
                    accion_duplicados = "eliminados"

        else:
            log_a_interfaz("✅ No se encontraron archivos duplicados.")

    else:
        # En simulación no hay movimientos reales, deshabilitar deshacer
        ultimo_movimiento = []
        boton_deshacer.config(state="disabled")

    # Construir mensaje final
    if es_simulacion:
        mensaje = "Simulación completada. Revisa el registro para ver qué se haría."
    else:
        if errores:
            mensaje = f"Se movieron {movidos} archivos, pero {len(errores)} tuvieron errores.\n"
        else:
            mensaje = f"¡Éxito! {movidos} archivos organizados correctamente.\n"

        # Agregar información sobre duplicados
        if accion_duplicados == "movidos":
            mensaje += f"Se movieron {cantidad_duplicados} archivos duplicados a la carpeta 'Duplicados'."
        elif accion_duplicados == "eliminados":
            mensaje += f"Se eliminaron {cantidad_duplicados} archivos duplicados (enviados a la papelera)."
        else:
            mensaje += "No se encontraron archivos duplicados."

    messagebox.showinfo("Resultado", mensaje)

# ---------- INTERFAZ GRÁFICA ----------

root = tk.Tk()
root.title("Organizador de Archivos")
root.geometry("700x550")
root.minsize(600, 450)
root.configure(bg="#2C3E50")

frame_principal = tk.Frame(root, bg="#2C3E50")
frame_principal.pack(expand=True, fill="both", padx=20, pady=20)

# Título
titulo = tk.Label(
    frame_principal,
    text="📁 Organizador de Archivos",
    font=("Helvetica", 24, "bold"),
    fg="#ECF0F1",
    bg="#2C3E50"
)
titulo.pack(pady=(0, 10))

# Subtítulo
subtitulo = tk.Label(
    frame_principal,
    text="Organiza tus archivos automáticamente por tipo",
    font=("Helvetica", 12),
    fg="#BDC3C7",
    bg="#2C3E50"
)
subtitulo.pack(pady=(0, 20))

# Etiqueta de carpeta seleccionada
etiqueta_carpeta = tk.Label(
    frame_principal,
    text="No se ha seleccionado ninguna carpeta",
    font=("Helvetica", 10, "italic"),
    fg="#95A5A6",
    bg="#2C3E50"
)
etiqueta_carpeta.pack(pady=(0, 10))

# Checkbutton para modo simulación
modo_simulacion = tk.BooleanVar(value=False)
check_simulacion = tk.Checkbutton(
    frame_principal,
    text="Modo simulación (no mover archivos)",
    variable=modo_simulacion,
    font=("Helvetica", 10),
    bg="#2C3E50",
    fg="#ECF0F1",
    selectcolor="#2C3E50",
    activebackground="#2C3E50",
    activeforeground="#ECF0F1",
    cursor="hand2"
)
check_simulacion.pack(pady=(0, 10))

# Botón para organizar
boton = tk.Button(
    frame_principal,
    text="Seleccionar carpeta y organizar",
    font=("Helvetica", 14, "bold"),
    bg="#3498DB",
    fg="white",
    activebackground="#2980B9",
    activeforeground="white",
    relief="flat",
    bd=0,
    padx=20,
    pady=15,
    cursor="hand2",
    command=seleccionar_carpeta_y_organizar
)
boton.pack(pady=(0, 10))

# Botón de deshacer
boton_deshacer = tk.Button(
    frame_principal,
    text="↩️ Deshacer última organización",
    font=("Helvetica", 12),
    bg="#E67E22",
    fg="white",
    activebackground="#D35400",
    activeforeground="white",
    relief="flat",
    bd=0,
    padx=15,
    pady=10,
    cursor="hand2",
    state="disabled",   # Inicialmente deshabilitado
    command=deshacer_ultima_organizacion
)
boton_deshacer.pack(pady=(0, 10))

# Barra de progreso
barra_progreso = ttk.Progressbar(
    frame_principal,
    orient="horizontal",
    length=400,
    mode="determinate"
)
barra_progreso.pack(pady=(10, 5), fill="x")


# Área de registro (Text + Scrollbar)
frame_texto = tk.Frame(frame_principal, bg="#2C3E50")
frame_texto.pack(fill="both", expand=True, pady=(5, 0))

scrollbar = tk.Scrollbar(frame_texto)
scrollbar.pack(side="right", fill="y")

area_texto = tk.Text(
    frame_texto,
    height=10,
    yscrollcommand=scrollbar.set,
    font=("Consolas", 9),
    bg="#1E2A38",
    fg="#ECF0F1",
    relief="flat",
    padx=5,
    pady=5,
    wrap="word"
)
area_texto.pack(side="left", fill="both", expand=True)
scrollbar.config(command=area_texto.yview)

# Pie de página
pie = tk.Label(
    root,
    text="v1.1 - Modo simulación agregado",
    font=("Helvetica", 8),
    fg="#7F8C8D",
    bg="#2C3E50"
)
pie.pack(side="bottom", pady=5)

root.mainloop()