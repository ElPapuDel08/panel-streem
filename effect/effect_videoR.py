# effect/effect_videoR.py
import os
import sys
import tkinter as tk
import threading
import random
import ctypes
import time

# === METADATOS ===
NOMBRE = "videoR"
VERSION = "1.4"

# === FUNCIONES AUXILIARES ===
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

# === FUNCIÓN PARA LISTAR VIDEOS DISPONIBLES ===
def listar_sub_efectos():
    """Descubre videos en video/ y los devuelve con el prefijo 'video_'."""
    ruta_videos = "video"
    if not os.path.exists(ruta_videos):
        return []

    sub_efectos = []
    for f in os.listdir(ruta_videos):
        if f.endswith('.mp4'):
            partes = f.split('_', 1)
            if partes and partes[0].isdigit():
                nombre = os.path.splitext(f)[0]
                sub_efectos.append(f"video_{nombre}")
    
    return sorted(sub_efectos)

# === FUNCIÓN PARA REPRODUCIR VIDEO ESPECÍFICO ===
def ejecutar_especifico(nombre_especifico, duracion_ms=None, volumen=100, parent=None, done_event=None):
    """
    Reproduce un archivo MP4 específico.
    """
    try:
        import vlc
    except ImportError:
        return {"error": "Efecto 'videoR' requiere 'python-vlc'."}

    nombre_archivo = nombre_especifico.replace("video_", "")
    volumen = max(0, min(100, int(volumen) if volumen is not None else 100))
    ruta_completa = os.path.join("video", f"{nombre_archivo}.mp4")
    
    if not os.path.exists(ruta_completa):
        return {"error": f"Archivo '{nombre_archivo}.mp4' no encontrado."}

    sw, sh = (parent.winfo_screenwidth(), parent.winfo_screenheight()) if parent else (1920, 1080)
    ALTURA, ANCHO = 256, 341 
    x, y = random.randint(0, max(0, sw - ANCHO)), random.randint(0, max(0, sh - ALTURA))

    if parent:
        # En el stage persistente, usamos una ventana Toplevel pero hija de parent
        # para que aparezca "encima" de ese lienzo específico.
        # O mejor, un Frame sobre el parent.
        container = tk.Frame(parent, width=ANCHO, height=ALTURA, bg=parent["bg"])
        container.place(x=x, y=y)
        win_id = container.winfo_id()
    else:
        root = crear_ventana_base()
        root.geometry(f"{ANCHO}x{ALTURA}+{x}+{y}")
        win_id = root.winfo_id()

    try:
        instance = vlc.Instance("--no-xlib", "--quiet")
        player = instance.media_player_new()
        player.set_hwnd(win_id)
        player.set_media(instance.media_new(os.path.abspath(ruta_completa)))
        player.audio_set_volume(volumen)
    except Exception as e:
        return {"error": f"VLC Error: {str(e)}"}

    inicio_real = None
    timer_activo = True
    
    def cerrar():
        nonlocal timer_activo
        if timer_activo:
            timer_activo = False
            try: player.stop(); player.release(); instance.release()
            except: pass
            if parent: container.destroy()
            else: root.destroy()
            if done_event: done_event.set()

    def gestionar():
        nonlocal inicio_real
        if not timer_activo: return
        try:
            if player.get_state() in (vlc.State.Ended, vlc.State.Error):
                cerrar(); return
            if player.get_time() > 0 and inicio_real is None:
                inicio_real = time.time()
            if duracion_ms and inicio_real and (time.time() - inicio_real)*1000 >= duracion_ms:
                cerrar(); return
            (container if parent else root).after(50, gestionar)
        except: 
            cerrar()
            if done_event: done_event.set()

    player.play()
    (container if parent else root).after(100, gestionar)
    if not parent:
        root.protocol("WM_DELETE_WINDOW", cerrar)
        root.mainloop()
    
    return {"mensaje": f"Video '{nombre_archivo}' reproducido."}

# === FUNClÓN PRINCIPAL ===
def ejecutar(duracion_ms=None, volumen=100, sub_tipo='NULL', cantidad=1, parent=None):
    done_event = threading.Event()
    for i in range(cantidad):
        if sub_tipo == 'NULL':
            ruta_videos = "video"
            if not os.path.exists(ruta_videos): return {"error": "video/ no found"}
            archivos = [f for f in os.listdir(ruta_videos) if f.endswith('.mp4') and f.split('_', 1)[0].isdigit()]
            if not archivos: return {"error": "no valid videos"}
            nombre_a_ejecutar = os.path.splitext(random.choice(archivos))[0]
        else:
            nombre_a_ejecutar = sub_tipo

        res = ejecutar_especifico(nombre_a_ejecutar, duracion_ms, volumen, parent=parent, done_event=done_event)
        
        # Esperar a que el video termine
        done_event.wait()
        done_event.clear()
        
        if "error" in res: return res
        if i < cantidad - 1: time.sleep(0.1)
            
    return {"mensaje": f"Efecto '{NOMBRE}' ejecutado {cantidad} veces."}
