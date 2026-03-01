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
# Agregamos la ruta base al principio de sys.path para que Python prefiera
# cargar los archivos .py de la carpeta física antes que los empaquetados en el EXE.
if base_path not in sys.path:
    sys.path.insert(0, base_path)

import time
import traceback
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# Ahora la importación buscará primero en la carpeta 'core' externa
from ui.panel import MainPanel

# ===== MANEJADOR DE ERRORES GLOBAL (ACTUALIZADO) =====
def manejar_error_global(exc_type, exc_value, exc_traceback):
    """
    Registra errores y muestra ventana de error NATIVA.
    Usa messagebox.showerror para mantener consistencia con el panel.
    """
    # Registrar en log.txt
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n{time.ctime()}\n{error_msg}\n{'='*50}\n")
    
    # Mostrar ventana de error nativa (Estilo Consistente)
    try:
        messagebox.showerror(
            title="💥 Error Crítico",
            message=f"El programa ha encontrado un error inesperado.\n\nDetalle: {str(exc_value)}\n\nSe ha guardado un registro en 'log.txt'.",
            parent=root  # parent no está definido aquí, messagebox maneja bien la ventana madre o por defecto
        )
        # Opcional: Si quieres permitir copiar al portapapeles o cerrar:
        # respuesta = messagebox.askyesno("Error", "El programa falló. ¿Deseas salir?")
    except:
        # Fallback en caso de error de UI
        print(f"CRASH FATAL: {exc_value}")
        print(error_msg)
        input("Presiona Enter para salir...")
    
    os._exit(1)

sys.excepthook = manejar_error_global

# ===== INICIALIZACIÓN DEL ORQUESTADOR =====
if __name__ == "__main__":
    try:
        # Configuración del color de transparencia para la pantalla de carga
        CROMA = 'white'

        # Crear ventana principal (oculta inicialmente)
        root = tk.Tk()
        root.withdraw()
        
        # --- Pantalla de Carga ---
        loading = tk.Toplevel(root)
        loading.title("Cargando...")
        loading.overrideredirect(True)
        loading.config(bg=CROMA)
        
        try:
            # Cargar imagen PNG con transparencia
            original_img = Image.open("loading.png")
            
            # Asegurar modo RGBA
            if original_img.mode != 'RGBA':
                original_img = original_img.convert('RGBA')
            
            # Escalar imagen
            new_size = (original_img.width // 3, original_img.height // 3)
            scaled_img = original_img.resize(new_size, Image.LANCZOS)
            loading_img = ImageTk.PhotoImage(scaled_img)
            
            # Etiqueta de la imagen
            loading_label = tk.Label(
                loading, 
                image=loading_img, 
                borderwidth=0,
                highlightthickness=0,
                bg=CROMA
            )
            loading_label.image = loading_img
            loading_label.pack()
            
            # Configurar transparencia de ventana
            loading.wm_attributes('-transparentcolor', CROMA)
            loading.config(bg=CROMA)
            
            # Centrar en pantalla
            screen_width = loading.winfo_screenwidth()
            screen_height = loading.winfo_screenheight()
            x = (screen_width // 2) - (scaled_img.width // 2)
            y = (screen_height // 2) - (scaled_img.height // 2)
            loading.geometry(f"{scaled_img.width}x{scaled_img.height}+{x}+{y}")
        except Exception as e:
            print("Advertencia: No se pudo cargar loading.png", e)
            loading.destroy()
            
        loading.update()
        
        # --- Inicializar la Aplicación Principal ---
        # Aquí instanciamos MainPanel desde ui/panel.py
        app = MainPanel(root)
        
        # Destruir pantalla de carga y mostrar ventana principal
        if loading.winfo_exists():
            loading.destroy()
        
        root.deiconify()
        root.mainloop()
        
    except Exception as e:
        # Llamamos al manejador global si falla la inicialización
        manejar_error_global(type(e), e, e.__traceback__)