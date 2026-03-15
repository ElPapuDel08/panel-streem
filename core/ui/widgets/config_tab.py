# core/ui/widgets/config_tab.py
import tkinter as tk
from tkinter import ttk

class ConfigTab:
    def __init__(self, parent_frame, main_panel):
        self.parent = parent_frame
        self.panel = main_panel
        self.setup_ui()

    def setup_ui(self):
        canvas = tk.Canvas(self.parent, highlightthickness=0, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        main_content = ttk.Frame(scrollable_frame)
        main_content.pack(fill="x", padx=10, pady=10)

        # --- SECCIÓN 1: CONFIGURACIÓN DE MENSAJES ---
        frame_msg = ttk.LabelFrame(main_content, text=" Mensajes ")
        frame_msg.pack(fill="x", pady=5)

        ttk.Label(frame_msg, text="Mensaje Follow:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.panel.ent_msg_follow = ttk.Entry(frame_msg, width=50, font=("Segoe UI", 9))
        self.panel.ent_msg_follow.insert(0, self.panel.config_data["msg_follow"])
        self.panel.ent_msg_follow.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 10))

        ttk.Label(frame_msg, text="Mensaje Gift:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.panel.ent_msg_gift = ttk.Entry(frame_msg, width=50, font=("Segoe UI", 9))
        self.panel.ent_msg_gift.insert(0, self.panel.config_data["msg_gift"])
        self.panel.ent_msg_gift.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 10))

        ttk.Label(frame_msg, text="Delay (segundos):").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(frame_msg, from_=0, to=10, increment=0.5, width=10, textvariable=self.panel.delay_val).grid(row=4, column=1, sticky="e", padx=5, pady=2)
        
        ttk.Checkbutton(frame_msg, text="Priorizar Regalos/Follows (Saltar delay)", variable=self.panel.skip_delay).grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # --- SECCIÓN 2: LECTURA DE VOZ ---
        frame_voice = ttk.LabelFrame(main_content, text=" Lectura de Voz (TTS) ")
        frame_voice.pack(fill="x", pady=10)

        grid_voice = ttk.Frame(frame_voice)
        grid_voice.pack(fill="x", padx=5, pady=5)
        
        ttk.Checkbutton(grid_voice, text="🔊 Leer Chat", variable=self.panel.voice_chat).grid(row=0, column=0, sticky="w", padx=5)
        ttk.Checkbutton(grid_voice, text="🔊 Leer Seguidores", variable=self.panel.voice_follow).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Checkbutton(grid_voice, text="🔊 Leer Regalos", variable=self.panel.voice_gift).grid(row=1, column=0, sticky="w", padx=5)
        ttk.Checkbutton(grid_voice, text="😎 Leer Emojis", variable=self.panel.read_emojis).grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(frame_voice, text="Modo lectura de Chat:").pack(anchor="w", padx=10, pady=(5, 0))
        mode_frame = ttk.Frame(frame_voice)
        mode_frame.pack(fill="x", padx=10, pady=5)
        ttk.Radiobutton(mode_frame, text="Leer todo", variable=self.panel.tts_mode, value="all").pack(side="left", padx=5)
        ttk.Radiobutton(mode_frame, text="Solo '!s'", variable=self.panel.tts_mode, value="command").pack(side="left", padx=5)

        # --- SECCIÓN 3: VOLUMEN ---
        frame_vol = ttk.LabelFrame(main_content, text=" Control de Volumen ")
        frame_vol.pack(fill="x", pady=5)

        ttk.Label(frame_vol, text="Volumen Voz (TTS):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        vol_tts_scale = ttk.Scale(frame_vol, from_=0, to=100, orient="horizontal", variable=self.panel.volume_tts_val)
        vol_tts_scale.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(frame_vol, text="Volumen Efectos:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        vol_eff_scale = ttk.Scale(frame_vol, from_=0, to=100, orient="horizontal", variable=self.panel.volume_effects_val)
        vol_eff_scale.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        frame_vol.columnconfigure(1, weight=1)

        # --- SECCIÓN 4: SISTEMA Y CONEXIÓN ---
        frame_sys = ttk.LabelFrame(main_content, text=" Sistema y Conexión ")
        frame_sys.pack(fill="x", pady=5)

        grid_sys = ttk.Frame(frame_sys)
        grid_sys.pack(fill="x", padx=5, pady=5)

        ttk.Checkbutton(grid_sys, text="🎬 Activar Efectos de Animación", variable=self.panel.filters_enabled).grid(row=0, column=0, sticky="w", padx=5)
        ttk.Checkbutton(grid_sys, text="🔇 Silenciar Fondo al reproducir efectos", variable=self.panel.allow_effects_mute).grid(row=1, column=0, sticky="w", padx=5)

        ttk.Label(grid_sys, text="Reconexión (seg):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(grid_sys, from_=1, to=60, width=5, textvariable=self.panel.reconnect_interval).grid(row=2, column=1, sticky="e", padx=5, pady=2)

        ttk.Label(grid_sys, text="Intentos máximos:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(grid_sys, from_=1, to=100, width=5, textvariable=self.panel.reconnect_attempts).grid(row=3, column=1, sticky="e", padx=5, pady=2)

        # --- SECCIÓN 5: OPTIMIZACIÓN Y SLOTS ---
        frame_slots = ttk.LabelFrame(main_content, text=" Optimización y Superposición (Slots) ")
        frame_slots.pack(fill="x", pady=5)

        grid_slots = ttk.Frame(frame_slots)
        grid_slots.pack(fill="x", padx=5, pady=5)

        ttk.Label(grid_slots, text="Máx. Efectos Simultáneos (por tipo):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(grid_slots, from_=1, to=10, width=5, textvariable=self.panel.max_concurrency).grid(row=0, column=1, sticky="e", padx=5, pady=2)

        ttk.Label(grid_slots, text="Retraso en Combo Escalera (seg):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(grid_slots, from_=0.1, to=5.0, increment=0.1, width=5, textvariable=self.panel.delay_combo).grid(row=1, column=1, sticky="e", padx=5, pady=2)
