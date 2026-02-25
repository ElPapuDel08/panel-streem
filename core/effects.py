# test_panel.py
import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os

class TestPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("🧪 Panel de Pruebas de Efectos")
        self.root.geometry("450x550")

        # Configuración global
        self.tiempo_global = tk.IntVar(value=10)
        self.volumen_global = tk.IntVar(value=100)

        # Detectar efectos
        self.efectos = self.detectar_efectos()
        self.setup_ui()

    def detectar_efectos(self):
        if not os.path.exists("core/gift_anim.py"):
            return []
        try:
            result = subprocess.run(
                [sys.executable, "core/gift_anim.py", "--list-effects"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.strip().splitlines() 
                        if line.strip() and not line.startswith("pygame")]
        except Exception as e:
            print("Error al detectar efectos:", e)
        return []

    def setup_ui(self):
        # Título
        ttk.Label(self.root, text="🧪 Panel de Pruebas", font=("Segoe UI", 14, "bold")).pack(pady=10)

        # Tiempo global
        frame_tiempo = ttk.Frame(self.root)
        frame_tiempo.pack(pady=5)
        ttk.Label(frame_tiempo, text="Tiempo (s):").pack(side="left")
        ttk.Spinbox(
            frame_tiempo, from_=0, to=60, width=5,
            textvariable=self.tiempo_global
        ).pack(side="left", padx=5)

        # Volumen global
        frame_volumen = ttk.Frame(self.root)
        frame_volumen.pack(pady=5)
        ttk.Label(frame_volumen, text="Volumen (%):").pack(side="left")
        ttk.Spinbox(
            frame_volumen, from_=0, to=100, width=5,
            textvariable=self.volumen_global
        ).pack(side="left", padx=5)

        # Separador
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=10)

        # Frame con scroll para los botones de efectos
        if not self.efectos:
            ttk.Label(self.root, text="⚠️ No se encontraron efectos.", foreground="red").pack(pady=10)
            return

        ttk.Label(self.root, text="Efectos disponibles:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20)

        # 👇 FRAME CON SCROLL AUTOMÁTICO
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Empaquetar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Añadir botones al frame con scroll
        for efecto in self.efectos:
            btn = ttk.Button(
                scrollable_frame,
                text=f"▶ Ejecutar '{efecto}'",
                command=lambda e=efecto: self.ejecutar_efecto(e)
            )
            btn.pack(pady=3, fill="x")

        # 👇 HABILITAR SCROLL CON LA RUEDA DEL MOUSE
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Vincular scroll al canvas y al frame scrollable
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

        # Instrucciones
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(
            self.root,
            text=(
                "ℹ️ Notas:\n"
                "- Usa tiempo=0 para reproducir sin límite (sonido/video completos).\n"
                "- El volumen (0-100%) afecta solo a efectos con audio."
            ),
            foreground="gray",
            justify="left"
        ).pack(pady=5)

    def ejecutar_efecto(self, nombre):
        if not os.path.exists("core/gift_anim.py"):
            return
        try:
            dur = self.tiempo_global.get()
            vol = self.volumen_global.get()
            
            # Formato estándar de 5 argumentos: [efecto, sub_tipo, segundos, volumen, cantidad]
            subprocess.Popen(
                [sys.executable, "core/gift_anim.py", nombre, "NULL", str(dur), str(vol), "1"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"Error al ejecutar '{nombre}': {e}")

if __name__ == "__main__":
    if not os.path.exists("core/gift_anim.py"):
        print("❌ Error: gift_anim.py no encontrado.")
        input("Presiona Enter para salir...")
        sys.exit(1)

    root = tk.Tk()
    ttk.Style().theme_use("clam")
    app = TestPanel(root)
    root.mainloop()