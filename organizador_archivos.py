import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from pathlib import Path
from categorias import categorias
import hashlib
from send2trash import send2trash
from ia_clasificador import clasificar_por_ia
import queue
import threading

# Variables globales
ultimo_movimiento = []            # Historial para deshacer
resultado_organizacion = None     # Guarda (movidos, errores, movimientos) del hilo
cola_mensajes = queue.Queue()     # Cola de comunicación hilo -> GUI

# ---------- FUNCIONES DE LÓGICA ----------

def listar_archivos(ruta):
    """Devuelve una lista con los Path de todos los archivos en la carpeta."""
    archivos = []
    for archivo in ruta.iterdir():
        if archivo.is_file():
            archivos.append(archivo)
    return archivos

def clasificar_archivo(archivo):
    """Clasifica un archivo según su extensión."""
    extension = archivo.suffix.lower()
    return categorias.get(extension, "Otros")

def obtener_destino_unico(destino):
    """Devuelve un destino que no existe, añadiendo _1, _2, etc. si es necesario."""
    if not destino.exists():
        return destino
    contador = 1
    while True:
        nuevo = destino.with_name(f"{destino.stem}_{contador}{destino.suffix}")
        if not nuevo.exists():
            return nuevo
        contador += 1

def listar_archivos_recursivo(ruta):
    """Lista archivos recursivamente."""
    archivos = []
    for elemento in ruta.rglob('*'):
        if elemento.is_file():
            archivos.append(elemento)
    return archivos

def detectar_duplicados(ruta):
    """Detecta grupos de archivos con contenido idéntico."""
    archivos = listar_archivos_recursivo(ruta)
    por_tamano = {}
    for archivo in archivos:
        try:
            tam = archivo.stat().st_size
            por_tamano.setdefault(tam, []).append(archivo)
        except:
            pass
    grupos_finales = []
    for tam, lista in por_tamano.items():
        if len(lista) < 2:
            continue
        grupos_hash = {}
        for archivo in lista:
            try:
                contenido = archivo.read_bytes()
                h = hashlib.md5(contenido).hexdigest()
                grupos_hash.setdefault(h, []).append(archivo)
            except:
                pass
        for grupo in grupos_hash.values():
            if len(grupo) > 1:
                grupos_finales.append(grupo)
    return grupos_finales

def organizar_archivos(ruta, simulacion=False, registro=None, progreso=None, usar_ia=False):
    """Organiza archivos en subcarpetas. No bloquea la GUI si se llama desde hilo."""
    archivos = listar_archivos(ruta)
    movidos = 0
    errores = []
    movimientos = []
    script_actual = Path(__file__).name

    total_archivos = sum(1 for a in archivos if a.name != script_actual)
    procesados = 0

    def log(mensaje):
        if registro:
            registro(mensaje)
        else:
            print(mensaje)

    for archivo in archivos:
        if archivo.name == script_actual:
            continue

        procesados += 1
        if progreso:
            progreso(procesados / total_archivos if total_archivos > 0 else 1)

        try:
            categoria = clasificar_archivo(archivo)
            carpeta_destino = ruta / categoria

            if usar_ia:
                tema = clasificar_por_ia(archivo.stem)
                if tema:
                    carpeta_destino = ruta / categoria / tema.capitalize()
                else:
                    carpeta_destino = ruta / categoria
            else:
                carpeta_destino = ruta / categoria

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
    return movidos, errores, movimientos

def mover_duplicados_a_carpeta(ruta, grupos_duplicados):
    """Mueve los duplicados (excepto el primero) a la carpeta 'Duplicados'."""
    carpeta_duplicados = ruta / "Duplicados"
    carpeta_duplicados.mkdir(exist_ok=True)
    movidos = 0
    movimientos = []
    for grupo in grupos_duplicados:
        for archivo in grupo[1:]:
            destino = carpeta_duplicados / archivo.name
            destino_final = obtener_destino_unico(destino)
            try:
                archivo.rename(destino_final)
                log_a_interfaz(f"🔁 Movido duplicado: {archivo.name} → Duplicados/{destino_final.name}")
                movidos += 1
                movimientos.append((archivo, destino_final))
            except Exception as e:
                log_a_interfaz(f"❌ Error al mover {archivo.name}: {e}")
    return movidos, movimientos

def eliminar_duplicados(grupos_duplicados):
    """Envía los duplicados a la papelera."""
    eliminados = 0
    for grupo in grupos_duplicados:
        for archivo in grupo[1:]:
            try:
                send2trash(str(archivo))
                log_a_interfaz(f"🗑️ Eliminado (papelera): {archivo.name}")
                eliminados += 1
            except Exception as e:
                log_a_interfaz(f"❌ Error al eliminar {archivo.name}: {e}")
    return eliminados

# ---------- FUNCIONES DE COMUNICACIÓN HILO -> GUI ----------

def encolar_mensaje(mensaje):
    cola_mensajes.put(("log", mensaje))

def encolar_progreso(valor):
    cola_mensajes.put(("progreso", valor))

def procesar_cola():
    """Revisa la cola y actualiza la GUI. Se llama periódicamente con root.after."""
    try:
        while True:
            tipo, valor = cola_mensajes.get_nowait()
            if tipo == "log":
                area_texto.insert(tk.END, valor + "\n")
                area_texto.see(tk.END)
            elif tipo == "progreso":
                barra_progreso["value"] = valor * 100
            elif tipo == "fin":
                finalizar_organizacion()
    except queue.Empty:
        pass
    root.after(100, procesar_cola)

# ---------- FUNCIONES DE LA INTERFAZ ----------

def log_a_interfaz(mensaje):
    """Inserta directamente en el área de texto (solo para hilo principal)."""
    area_texto.insert(tk.END, mensaje + "\n")
    area_texto.see(tk.END)

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
            if destino.exists():
                destino.rename(origen)
                log_a_interfaz(f"↩️ Revertido: {destino.name} → {origen.parent.name}/")
        except Exception as e:
            log_a_interfaz(f"❌ Error al revertir {destino.name}: {e}")
    ultimo_movimiento = []
    boton_deshacer.config(state="disabled")
    messagebox.showinfo("Deshacer", "Operación de deshacer completada.")

def seleccionar_carpeta_y_organizar():
    """Inicia la organización en un hilo secundario."""
    global ultimo_movimiento, resultado_organizacion
    carpeta = filedialog.askdirectory()
    if not carpeta:
        return

    area_texto.delete(1.0, tk.END)
    etiqueta_carpeta.config(text=f"📂 {carpeta}")
    barra_progreso["value"] = 0
    boton.config(state="disabled")   # Desactivar botón para evitar doble clic

    es_simulacion = modo_simulacion.get()
    usar_ia = modo_ia.get()

    # Crear hilo y ejecutar
    hilo = threading.Thread(
        target=hilo_organizar,
        args=(Path(carpeta), es_simulacion, usar_ia),
        daemon=True
    )
    hilo.start()

def hilo_organizar(ruta, es_simulacion, usar_ia):
    """Función ejecutada en segundo plano. Realiza la organización y encola resultados."""
    global resultado_organizacion
    # Llamar a la función que hace el trabajo real
    movidos, errores, movimientos = organizar_archivos(
        ruta,
        simulacion=es_simulacion,
        registro=encolar_mensaje,
        progreso=encolar_progreso,
        usar_ia=usar_ia
    )
    # Guardar resultado en variable global para que el hilo principal lo use
    resultado_organizacion = (movidos, errores, movimientos, es_simulacion)
    # Encolar mensaje de fin
    cola_mensajes.put(("fin", None))

def finalizar_organizacion():
    """Se ejecuta en el hilo principal cuando el hilo secundario termina."""
    global ultimo_movimiento
    movidos, errores, movimientos, es_simulacion = resultado_organizacion

    if not es_simulacion:
        # Guardar historial para deshacer
        ultimo_movimiento = movimientos
        boton_deshacer.config(state="normal")

        # Detección de duplicados
        grupos_duplicados = detectar_duplicados(Path(etiqueta_carpeta.cget("text").replace("📂 ", "")))
        if grupos_duplicados:
            respuesta = messagebox.askyesno(
                "Duplicados encontrados",
                f"Se encontraron {len(grupos_duplicados)} grupos de archivos duplicados.\n"
                "¿Desea mover los duplicados a la carpeta 'Duplicados'?\n"
                "Seleccione 'No' para eliminarlos."
            )
            if respuesta:
                mov_dup, movimientos_dup = mover_duplicados_a_carpeta(Path(etiqueta_carpeta.cget("text").replace("📂 ", "")), grupos_duplicados)
                if movimientos_dup:
                    ultimo_movimiento = movimientos + movimientos_dup
                    boton_deshacer.config(state="normal")
                cantidad_duplicados = mov_dup
                accion_duplicados = "movidos"
            else:
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
                    accion_duplicados = None
            if accion_duplicados:
                log_a_interfaz(f"Duplicados {accion_duplicados}: {cantidad_duplicados}")
        else:
            log_a_interfaz("✅ No se encontraron archivos duplicados.")
    else:
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
        if 'accion_duplicados' in locals() and accion_duplicados:
            if accion_duplicados == "movidos":
                mensaje += f"Se movieron {cantidad_duplicados} duplicados a 'Duplicados'."
            else:
                mensaje += f"Se eliminaron {cantidad_duplicados} duplicados (papelera)."
        else:
            mensaje += "No se encontraron duplicados."
    messagebox.showinfo("Resultado", mensaje)
    boton.config(state="normal")   # Reactivar botón

# ---------- INTERFAZ GRÁFICA ----------
root = tk.Tk()
root.title("Organizador de Archivos")
root.geometry("700x550")
root.minsize(600, 450)
root.configure(bg="#2C3E50")

frame_principal = tk.Frame(root, bg="#2C3E50")
frame_principal.pack(expand=True, fill="both", padx=20, pady=20)

titulo = tk.Label(frame_principal, text="📁 Organizador de Archivos", font=("Helvetica", 24, "bold"), fg="#ECF0F1", bg="#2C3E50")
titulo.pack(pady=(0, 10))

subtitulo = tk.Label(frame_principal, text="Organiza tus archivos automáticamente por tipo", font=("Helvetica", 12), fg="#BDC3C7", bg="#2C3E50")
subtitulo.pack(pady=(0, 20))

etiqueta_carpeta = tk.Label(frame_principal, text="No se ha seleccionado ninguna carpeta", font=("Helvetica", 10, "italic"), fg="#95A5A6", bg="#2C3E50")
etiqueta_carpeta.pack(pady=(0, 10))

modo_ia = tk.BooleanVar(value=False)
check_ia = tk.Checkbutton(frame_principal, text="🧠 Usar IA para subcategorías", variable=modo_ia, font=("Helvetica", 10), bg="#2C3E50", fg="#ECF0F1", selectcolor="#2C3E50", activebackground="#2C3E50", activeforeground="#ECF0F1", cursor="hand2")
check_ia.pack(pady=(0, 10))

modo_simulacion = tk.BooleanVar(value=False)
check_simulacion = tk.Checkbutton(frame_principal, text="Modo simulación (no mover archivos)", variable=modo_simulacion, font=("Helvetica", 10), bg="#2C3E50", fg="#ECF0F1", selectcolor="#2C3E50", activebackground="#2C3E50", activeforeground="#ECF0F1", cursor="hand2")
check_simulacion.pack(pady=(0, 10))

boton = tk.Button(frame_principal, text="Seleccionar carpeta y organizar", font=("Helvetica", 14, "bold"), bg="#3498DB", fg="white", activebackground="#2980B9", activeforeground="white", relief="flat", bd=0, padx=20, pady=15, cursor="hand2", command=seleccionar_carpeta_y_organizar)
boton.pack(pady=(0, 10))

boton_deshacer = tk.Button(frame_principal, text="↩️ Deshacer última organización", font=("Helvetica", 12), bg="#E67E22", fg="white", activebackground="#D35400", activeforeground="white", relief="flat", bd=0, padx=15, pady=10, cursor="hand2", state="disabled", command=deshacer_ultima_organizacion)
boton_deshacer.pack(pady=(0, 10))

barra_progreso = ttk.Progressbar(frame_principal, orient="horizontal", length=400, mode="determinate")
barra_progreso.pack(pady=(10, 5), fill="x")

frame_texto = tk.Frame(frame_principal, bg="#2C3E50")
frame_texto.pack(fill="both", expand=True, pady=(5, 0))

scrollbar = tk.Scrollbar(frame_texto)
scrollbar.pack(side="right", fill="y")

area_texto = tk.Text(frame_texto, height=10, yscrollcommand=scrollbar.set, font=("Consolas", 9), bg="#1E2A38", fg="#ECF0F1", relief="flat", padx=5, pady=5, wrap="word")
area_texto.pack(side="left", fill="both", expand=True)
scrollbar.config(command=area_texto.yview)

pie = tk.Label(root, text="v2.0 - Con hilos para no bloquear", font=("Helvetica", 8), fg="#7F8C8D", bg="#2C3E50")
pie.pack(side="bottom", pady=5)

# Iniciar el procesamiento de la cola
root.after(100, procesar_cola)

root.mainloop()