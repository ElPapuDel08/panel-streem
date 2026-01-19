# effect/effect_videos_list.py
import os
import tkinter as tk
import ctypes
import time

# === METADATOS ===
NOMBRE = "Lista de Videos"
LISTA = []

def cargar_archivos():
    """Escanea video/ y llena la lista global."""
    global LISTA
    LISTA = []
    ruta = "video"
    if not os.path.exists(ruta): return

    for f in os.listdir(ruta):
        if f.endswith('.mp4'):
            nombre = os.path.splitext(f)[0]
            LISTA.append(nombre)
    
    LISTA.sort()

# Ejecutamos carga al importar
cargar_archivos()

# === CONFIGURACIÓN DE VENTANA INVISIBLE ===
COLOR_FONDO = "#FF00FF"

def aplicar_estilo_fantasma(ventana):
    ventana.update_idletasks()
    hwnd = ctypes.windll.user32.GetParent(ventana.winfo_id())
    style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
    style |= 0x00000020
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)

def crear_ventana_base():
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.config(bg=COLOR_FONDO)
    root.attributes("-transparentcolor", COLOR_FONDO)
    aplicar_estilo_fantasma(root)
    return root

def ejecutar(nombre_archivo, duracion_ms=None, volumen=100):
    """
    Reproduce un video MP4 específico.
    """
    try:
        import vlc
    except ImportError:
        return {"error": "Efecto 'Lista de Videos' requiere 'python-vlc'. Ejecuta: pip install python-vlc"}

    volumen = max(0, min(100, int(volumen) if volumen is not None else 100))
    ruta_videos = "video"
    ruta_completa = os.path.join(ruta_videos, f"{nombre_archivo}.mp4")
    
    if not os.path.exists(ruta_completa):
        return {"error": f"Archivo '{nombre_archivo}.mp4' no encontrado."}

    # Configuración de ventana
    root = crear_ventana_base()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    ALTURA, ANCHO = 256, 341
    # Posición aleatoria
    x = 50 # Podríamos hacerlo random, pero para efecto específico es mejor tenerlo controlado o centrado
    y = 50
    root.geometry(f"{ANCHO}x{ALTURA}+{x}+{y}")

    # Inicializar VLC
    try:
        instance = vlc.Instance("--no-xlib", "--quiet")
        player = instance.media_player_new()
        player.set_hwnd(root.winfo_id())
        
        media = instance.media_new(os.path.abspath(ruta_completa))
        player.set_media(media)
        player.audio_set_volume(volumen)
    except Exception as e:
        return {"error": f"Error inicializando VLC: {str(e)}"}

    duracion_usada = duracion_ms
    inicio_real = None
    timer_activo = True
    
    def cerrar_ventana():
        nonlocal timer_activo
        if timer_activo:
            timer_activo = False
            try:
                player.stop()
                player.release()
                instance.release()
            except:
                pass
            root.destroy()

    def gestionar_reproduccion():
        nonlocal inicio_real, duracion_usada, timer_activo
        if not timer_activo: return
        
        try:
            estado = player.get_state()
            tiempo_actual = player.get_time()
            
            if inicio_real is None and tiempo_actual > 0:
                inicio_real = time.time()
            
            if estado in (vlc.State.Ended, vlc.State.Error):
                cerrar_ventana()
                return
            
            if duracion_usada is not None and duracion_usada > 0:
                if inicio_real is not None:
                    tiempo_transcurrido = (time.time() - inicio_real) * 1000
                    if tiempo_transcurrido >= duracion_usada:
                        cerrar_ventana()
                        return
            
            root.after(50, gestionar_reproduccion)
        except Exception:
            cerrar_ventana()

    player.play()
    root.after(100, gestionar_reproduccion)
    root.protocol("WM_DELETE_WINDOW", cerrar_ventana)
    root.mainloop()
    
    return {"mensaje": f"Video '{nombre_archivo}' reproducido."}