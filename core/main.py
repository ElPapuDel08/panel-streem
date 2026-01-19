# main.py
import sys
import os
import time
import traceback
import tkinter as tk
from PIL import Image, ImageTk

# Importamos el panel desde la carpeta ui
from ui.panel import MainPanel

# ===== MANEJADOR DE ERRORES GLOBAL =====
def manejar_error_global(exc_type, exc_value, exc_traceback):
    """Registra errores y muestra ventana de crash."""
    # Registrar en log.txt
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n{time.ctime()}\n{error_msg}\n{'='*50}\n")
    
    # Mostrar ventana de crash
    try:
        import tkinter.ttk as ttk
        crash_win = tk.Tk()
        crash_win.title("💥 CRASH")
        crash_win.geometry("500x200")
        crash_win.resizable(False, False)
        crash_win.eval('tk::PlaceWindow . center')
        
        msg = f"Oops... el programa tuvo un error\n\n{str(exc_value)}\n\nError guardado en log.txt"
        ttk.Label(crash_win, text=msg, wraplength=480, justify="center").pack(pady=20)
        ttk.Button(crash_win, text="Aceptar y cerrar", command=lambda: os._exit(1)).pack(pady=10)
        crash_win.mainloop()
    except:
        print("CRASH FATAL:")
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
        manejar_error_global(type(e), e, e.__traceback__)