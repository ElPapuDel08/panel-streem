# core/ui/widgets/control_tab.py
import tkinter as tk
from tkinter import ttk

class ControlTab:
    def __init__(self, parent_frame, main_panel):
        self.parent = parent_frame
        self.panel = main_panel
        self.setup_ui()

    def setup_ui(self):
        card = tk.Frame(self.parent, bg="#ffffff", bd=1, relief="solid")
        card.pack(fill="both", expand=True, padx=5, pady=5)
        
        inner = tk.Frame(card, bg="#ffffff")
        inner.pack(fill="both", expand=True, padx=15, pady=15)

        lbl_user = tk.Label(inner, text="Usuario de TikTok:", bg="#ffffff", font=("Segoe UI", 11, "bold"), fg="#2c3e50")
        lbl_user.pack(anchor="w", pady=(0, 5))
        
        self.panel.ent_user = tk.Entry(inner, font=("Segoe UI", 10), bg="#f9f9f9", bd=1)
        self.panel.ent_user.insert(0, self.panel.config_data["usuario_tiktok"])
        self.panel.ent_user.pack(fill="x", pady=(0, 15))

        frame_btns = tk.Frame(inner, bg="#ffffff")
        frame_btns.pack(pady=5)

        self.panel.btn_toggle = ttk.Button(frame_btns, text="▶ INICIAR LIVE", command=self.panel.toggle_bot, width=15)
        self.panel.btn_toggle.pack(side="left", padx=5)

        self.panel.btn_test = ttk.Button(frame_btns, text="🧪 PRE-VISUALIZADOR", command=self.panel.toggle_test_mode, width=15)
        self.panel.btn_test.pack(side="left", padx=5)

        lbl_log = tk.Label(inner, text="📜 Registro de Eventos:", bg="#ffffff", font=("Segoe UI", 11, "bold"), fg="#2c3e50")
        lbl_log.pack(anchor="w", pady=(15, 5))
        
        log_frame = tk.Frame(inner, bg="#1e1e1e", bd=1, relief="sunken")
        log_frame.pack(fill="both", expand=True)
        
        self.panel.log_txt = tk.Text(log_frame, height=10, width=60, state='disabled', font=("Consolas", 9), bg="#1e1e1e", fg="#00ff00", insertbackground="white", bd=0)
        self.panel.log_txt.pack(fill="both", expand=True, padx=5, pady=5)
