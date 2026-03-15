import sys
import os

# Determinar la ruta base (raíz del proyecto o carpeta del EXE)
if getattr(sys, 'frozen', False):
    # Si estamos en el EXE, la raíz es la carpeta donde está el .exe
    base_path = os.path.dirname(sys.executable)
else:
    # Si estamos ejecutando el script, la raíz es la carpeta padre de 'core'
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# PRIORIZAR ARCHIVOS EXTERNOS:
if base_path not in sys.path:
    sys.path.insert(0, base_path)

import time
import traceback
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# ===== MANEJADOR DE ERRORES GLOBAL =====
def manejar_error_global(exc_type, exc_value, exc_traceback):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n{time.ctime()}\n{error_msg}\n{'='*50}\n")
    
    try:
        messagebox.showerror(
            title="💥 Error Crítico",
            message=f"El programa ha encontrado un error inesperado.\n\nDetalle: {str(exc_value)}\n\nSe ha guardado un registro en 'log.txt'."
        )
    except:
        print(f"CRASH FATAL: {exc_value}")
        print(error_msg)
    
    os._exit(1)

sys.excepthook = manejar_error_global

# ===== DETECCIÓN DINÁMICA DE EVENTOS =====
def discover_events():
    events = {}
    ui_dir = os.path.join(base_path, "core", "ui")
    if os.path.exists(ui_dir):
        for f in os.listdir(ui_dir):
            if f.startswith("event_") and f.endswith(".py"):
                name = f[6:-3]
                events[name] = f"ui.{f[:-3]}"
    return events

# ===== PANTALLA DE CARGA (SPLASH SCREEN) =====
def create_loading_screen(root):
    """Crea una ventana de carga estética y la mantiene siempre al frente."""
    CROMA = 'white'
    loading = tk.Toplevel(root)
    loading.title("Cargando...")
    loading.overrideredirect(True)
    loading.attributes("-topmost", True) # SIEMPRE ADELANTE
    loading.config(bg=CROMA)
    
    try:
        if os.path.exists("loading.png"):
            original_img = Image.open("loading.png")
            if original_img.mode != 'RGBA':
                original_img = original_img.convert('RGBA')
            
            # Escalar imagen (1/3 del tamaño original)
            new_size = (original_img.width // 3, original_img.height // 3)
            scaled_img = original_img.resize(new_size, Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(scaled_img)
            
            lbl = tk.Label(loading, image=tk_img, borderwidth=0, highlightthickness=0, bg=CROMA)
            lbl.image = tk_img
            lbl.pack()
            
            loading.wm_attributes('-transparentcolor', CROMA)
            
            # Centrar en pantalla
            sw, sh = loading.winfo_screenwidth(), loading.winfo_screenheight()
            x = (sw // 2) - (scaled_img.width // 2)
            y = (sh // 2) - (scaled_img.height // 2)
            loading.geometry(f"{scaled_img.width}x{scaled_img.height}+{x}+{y}")
        else:
            # Fallback simple si no hay imagen
            tk.Label(loading, text="🚀 Cargando TikTok Panel Pro...", padx=20, pady=10, font=("Segoe UI", 12, "bold")).pack()
            loading.update()
            sw, sh = loading.winfo_screenwidth(), loading.winfo_screenheight()
            loading.geometry(f"+{(sw//2)-100}+{(sh//2)-30}")
    except Exception as e:
        print(f"Error en loading screen: {e}")
        loading.destroy()
        return None
        
    loading.update()
    return loading

# ===== INICIALIZACIÓN DEL ORQUESTADOR =====
if __name__ == "__main__":
    events = discover_events()
    arg = sys.argv[1].lower().replace("--", "") if len(sys.argv) > 1 else "panel"

    # Preparar base oculta para el Splash Screen
    root = tk.Tk()
    root.withdraw()
    
    splash = create_loading_screen(root)

    if arg == "panel":
        try:
            from ui.panel import MainPanel
            app = MainPanel(root)
            
            if splash and splash.winfo_exists():
                splash.destroy()
            
            root.deiconify()
            root.mainloop()
        except Exception as e:
            manejar_error_global(type(e), e, e.__traceback__)
    
    elif arg in events:
        try:
            import importlib
            print(f">>> Iniciando Evento Independiente: {arg}")
            module_name = events[arg]
            module = importlib.import_module(module_name)
            
            if splash and splash.winfo_exists():
                splash.destroy()

            if hasattr(module, "start"):
                module.start()
            else:
                print(f"⚠️ Módulo '{arg}' no tiene función 'start()'.")
        except Exception as e:
            manejar_error_global(type(e), e, e.__traceback__)
    else:
        if splash: splash.destroy()
        print(f"Error: Argumento '{arg}' no reconocido.")
        print("Uso: main.py [--panel | --nombre_evento]")
        if events:
            print("Eventos detectados:", ", ".join(events.keys()))
        sys.exit(1)