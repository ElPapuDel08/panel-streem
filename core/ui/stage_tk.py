# core/ui/stage_tk.py
import tkinter as tk

class StageManager:
    """
    Gestiona la ventana transparente (Stage) utilizada para renderizar efectos visuales.
    Desacoplado de MainPanel para mejorar la mantenibilidad.
    """
    def __init__(self, parent_root):
        self.root = parent_root
        self.window = tk.Toplevel(self.root)
        self.window.title("Efectos - Stage")
        
        # Configuración de transparencia y visualización
        self.window.attributes("-topmost", True)
        self.window.attributes("-fullscreen", True)
        self.window.config(bg="magenta")
        self.window.attributes("-transparentcolor", "magenta")
        
        # Lienzo persistente único para los efectos
        self.persistent_canvas = tk.Canvas(self.window, bg="magenta", highlightthickness=0, bd=0)
        self.persistent_canvas.pack(fill="both", expand=True)
        
        # Exponer el lienzo para compatibilidad con módulos de efectos existentes
        self.window.persistent_canvas = self.persistent_canvas
        
        # Impedir el cierre accidental
        self.window.protocol("WM_DELETE_WINDOW", lambda: None)

    def get_window(self):
        """Retorna la instancia de Toplevel (Stage)."""
        return self.window

    def get_canvas(self):
        """Retorna el lienzo persistente."""
        return self.persistent_canvas

    def destroy(self):
        """Cierra la ventana del Stage."""
        if self.window:
            self.window.destroy()
