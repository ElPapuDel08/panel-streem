import os
import sys
import tkinter as tk
import threading
from PIL import Image, ImageTk
import random
import ctypes
import time

# === METADATOS ===
NOMBRE = "boom"
VERSION = "1.1"

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

# === FUNCIÓN PRINCIPAL ===
def ejecutar(duracion_ms=None, volumen=100, sub_tipo='NULL', cantidad=1, parent=None):
    if duracion_ms == 0: return {"error": "boom = \"value invalid\""}
    ruta_iconos = "icon"
    if not os.path.exists(ruta_iconos): return {"error": "icon/ no found"}
    archivos = [f for f in os.listdir(ruta_iconos) if f.endswith('.png') and f.split('.')[0].isdigit()]
    if not archivos: return {"error": "no icons"}

    master = parent if parent else None
    imgs_tk = []
    for f in archivos:
        img = Image.open(os.path.join(ruta_iconos, f)).resize((32, 32), Image.LANCZOS)
        imgs_tk.append(ImageTk.PhotoImage(img, master=master))

    done_event = threading.Event()

    for _ in range(cantidad):
        if parent:
            # Usar el lienzo persistente compartido (Fijado en panel.py)
            canvas = getattr(parent, "persistent_canvas", None)
            sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
            
            if not canvas:
                # Fallback si por algún motivo no existe el compartido
                canvas = tk.Canvas(parent, width=sw, height=sh, bg=parent["bg"], highlightthickness=0, bd=0)
                canvas.place(x=0, y=0)
            
            iniciar_animacion(canvas, sw, sh, imgs_tk, duracion_ms, is_standalone=False, done_event=done_event)
        else:
            root = crear_ventana_base()
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            root.geometry(f"{sw}x{sh}+0+0")
            canvas = tk.Canvas(root, width=sw, height=sh, bg=COLOR_FONDO, highlightthickness=0, bd=0)
            canvas.pack()
            iniciar_animacion(canvas, sw, sh, imgs_tk, duracion_ms, is_standalone=True, root=root, done_event=done_event)
            
        done_event.wait()
        done_event.clear()
        time.sleep(0.1)
    return {"mensaje": f"Efecto '{NOMBRE}' ejecutado {cantidad} veces."}

def iniciar_animacion(canvas, sw, sh, imgs_tk, duracion_ms, is_standalone=True, root=None, done_event=None):
    particulas = []
    animando = True # Flag para detener el bucle
    
    def animar():
        if not animando: return
        try:
            if len(particulas) < 80:
                for _ in range(8):
                    pdx, pdy = random.uniform(-12, 12), random.uniform(-12, 12)
                    img_tk = random.choice(imgs_tk)
                    obj = canvas.create_image(sw//2, sh//2, image=img_tk)
                    particulas.append({'id': obj, 'x': sw//2, 'y': sh//2, 'dx': pdx, 'dy': pdy})
            
            for p in particulas[:]:
                p['x'] += p['dx']; p['y'] += p['dy']
                try:
                    canvas.coords(p['id'], p['x'], p['y'])
                except: pass

            canvas.after(20, animar)
        except: pass

    animar()

    def cleanup():
        nonlocal animando
        animando = False
        try:
            # Borrar solo nuestras partículas
            for p in particulas:
                try: canvas.delete(p['id'])
                except: pass
            
            if is_standalone and root: 
                try: root.destroy()
                except: pass
            elif not is_standalone and not hasattr(canvas.master, "persistent_canvas"):
                try: canvas.destroy()
                except: pass
                
            # Solo llamar al set una vez
            if done_event and not done_event.is_set():
                done_event.set()
        except: 
            if done_event and not done_event.is_set():
                done_event.set()

    canvas.after(duracion_ms if duracion_ms else 3000, cleanup)
