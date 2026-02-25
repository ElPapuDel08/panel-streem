# effect/effect_carta.py
import os
import sys
import tkinter as tk
import threading
from PIL import Image, ImageTk
import random
import ctypes
import time

# === METADATOS ===
NOMBRE = "carta"
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
    ruta_iconos = "icon"
    if not os.path.exists(ruta_iconos): return {"error": "icon/ no found"}
    archivos = [f for f in os.listdir(ruta_iconos) if f.endswith('.png')]
    if not archivos: return {"error": "no icons"}

    master = parent if parent else None
    
    # Seleccionar 3 imágenes al azar por cada instancia
    seleccion = random.sample(archivos, min(3, len(archivos)))
    imgs_tk = []
    
    for f in seleccion:
        # Volvemos a imágenes sólidas de alta calidad para máxima nitidez
        orig_img = Image.open(os.path.join(ruta_iconos, f)).resize((64, 90), Image.LANCZOS)
        imgs_tk.append(ImageTk.PhotoImage(orig_img, master=master))

    done_event = threading.Event()

    for _ in range(cantidad):
        if parent:
            canvas = getattr(parent, "persistent_canvas", None)
            sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
            if not canvas:
                canvas = tk.Canvas(parent, width=sw, height=sh, bg=parent["bg"], highlightthickness=0, bd=0)
                canvas.place(x=0, y=0)
            
            iniciar_animacion_solitario(canvas, sw, sh, imgs_tk, duracion_ms, is_standalone=False, done_event=done_event)
        else:
            root = crear_ventana_base()
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            root.geometry(f"{sw}x{sh}+0+0")
            canvas = tk.Canvas(root, width=sw, height=sh, bg=COLOR_FONDO, highlightthickness=0, bd=0)
            canvas.pack()
            iniciar_animacion_solitario(canvas, sw, sh, imgs_tk, duracion_ms, is_standalone=True, root=root, done_event=done_event)
            
        done_event.wait()
        done_event.clear()
        time.sleep(0.2)
        
    return {"mensaje": f"Efecto '{NOMBRE}' ejecutado {cantidad} veces."}

def iniciar_animacion_solitario(canvas, sw, sh, imgs_tk, duracion_ms, is_standalone=True, root=None, done_event=None):
    objetos = []
    for img_tk in imgs_tk:
        start_x = random.randint(100, sw-100)
        start_y = random.randint(50, 150)
        obj_id = canvas.create_image(start_x, start_y, image=img_tk)
        
        dx = random.uniform(7, 15) * random.choice([-1, 1])
        dy = random.uniform(-8, 2)
        
        objetos.append({
            'id': obj_id, 
            'x': start_x, 
            'y': start_y, 
            'dx': dx, 
            'dy': dy,
            'img': img_tk,
            'trail': [] # Lista de IDs de la estela
        })

    gravity = 0.95
    damping = 0.8
    animando = True # Flag para detener el bucle after

    def animar():
        if not animando: return
        try:
            for o in objetos:
                # Física básica
                o['dy'] += gravity
                o['x'] += o['dx']
                o['y'] += o['dy']

                # Rebote en el suelo
                if o['y'] >= sh - 45: 
                    o['y'] = sh - 45
                    o['dy'] *= -damping
                    if abs(o['dy']) < 3: o['dy'] = 0 
                
                # Rebote en paredes laterales
                if o['x'] <= 32 or o['x'] >= sw - 32:
                    o['dx'] *= -1

                # Rastro dinámico - Uno cada frame
                trail_id = canvas.create_image(o['x'], o['y'], image=o['img'])
                o['trail'].append(trail_id)
                
                # Límite de estela corto para que se vea cómo se pierde mientras avanza
                if len(o['trail']) > 35:
                    try: canvas.delete(o['trail'].pop(0))
                    except: pass

                # Actualizar carta principal (siempre encima)
                try:
                    canvas.coords(o['id'], o['x'], o['y'])
                    canvas.tag_raise(o['id'])
                except: pass

            canvas.after(30, animar)
        except: pass

    animar()

    def cleanup():
        nonlocal animando
        animando = False
        try:
            for o in objetos:
                try: canvas.delete(o['id'])
                except: pass
                for t_id in o['trail']:
                    try: canvas.delete(t_id)
                    except: pass
            
            if is_standalone and root: 
                try: root.destroy()
                except: pass
            elif not is_standalone and not hasattr(canvas.master, "persistent_canvas"):
                try: canvas.destroy()
                except: pass
                
            if done_event and not done_event.is_set():
                done_event.set()
        except: 
            if done_event and not done_event.is_set():
                done_event.set()

    canvas.after(duracion_ms if duracion_ms else 5000, cleanup)
