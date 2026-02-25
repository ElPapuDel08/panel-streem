# ui/panel.py
import tkinter as tk
from tkinter import ttk
import threading
import time
import os
import pygame
import json
from gtts import gTTS
from queue import Queue
import subprocess
import sys
import traceback
import re
import socket
from tkinter import messagebox

# === CONFIGURACIÓN DE RUTAS ===
# De core/ui/panel.py -> core/ui -> core -> raiz
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

# Importación del scraper
from content_tiktok import TikTokScraper
from core.ui.plugins import WorkshopManager

# ===== IMPORTACIÓN OPCIONAL DE PYCAW =====
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume
    from comtypes import CLSCTX_ALL
    from ctypes import cast, POINTER, oledll
    import comtypes
    HAS_PYCAW = True
except Exception:
    HAS_PYCAW = False

# ======================================================
# CLASE TOOLTIP PARA NOMBRES LARGOS
# ======================================================
class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.text = ""
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def update_text(self, new_text):
        self.text = new_text

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        # Solo mostrar si el widget es un Combobox y el texto es más largo de lo visible
        # o simplemente mostrarlo siempre para asegurar legibilidad como pidió el usuario.
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        tw.attributes("-topmost", True)
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#2c3e50", foreground="white", 
                         relief=tk.SOLID, borderwidth=1,
                         padx=5, pady=2,
                         font=("Segoe UI", "9", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

class MainPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Live Bot - Pro")
        self.root.geometry("650x600")
        self.root.configure(bg="#f0f0f0")

        self.queue = Queue()
        self.is_running = False
        self.is_testing = False
        self.test_window = None
        self.config_file = "core/profile/config.json"
        self.data_file = "core/data.json"
        
        # Lista para guardar sesiones silenciadas
        self.muted_sessions = [] 

        self.config_data = {
            "usuario_tiktok": "tu_usuario",
            "delay": 1.5,
            "skip_delay_priority": True,
            "msg_follow": "Gracias {user} por seguirme",
            "msg_gift": "{user} envió {cant} {gift}",
            "voice_chat": True,
            "voice_follow": True,
            "voice_gift": True,
            "read_emojis": True,
            "filters_enabled": True,
            "allow_effects_mute": True,
            "filtros": [], # Mantener por compatibilidad con config.json
            "comandos": ["!bola8"], # Nueva lista de comandos
            "eventos": ["Doughnut"],
            "reconnect_interval": 5,
            "reconnect_attempts": 10,
            "volume_tts": 100,
            "volume_effects": 100,
            "max_concurrency": 3,
            "delay_combo": 1.0
        }

        self.load_config()
        self.setup_styles()

        # Variables Tkinter
        self.voice_chat = tk.BooleanVar(value=self.config_data["voice_chat"])
        self.voice_follow = tk.BooleanVar(value=self.config_data["voice_follow"])
        self.voice_gift = tk.BooleanVar(value=self.config_data["voice_gift"])
        self.read_emojis = tk.BooleanVar(value=self.config_data.get("read_emojis", True))
        self.filters_enabled = tk.BooleanVar(value=self.config_data["filters_enabled"])
        self.allow_effects_mute = tk.BooleanVar(value=self.config_data.get("allow_effects_mute", True))
        
        # Concurrencia y Semáforos
        self.max_concurrency = tk.IntVar(value=self.config_data.get("max_concurrency", 3))
        self.delay_combo = tk.DoubleVar(value=self.config_data.get("delay_combo", 1.0))
        self.semaphores = {} # Se llenará dinámicamente por tipo de efecto

        # Efectos y UI
        self.efectos_slots = []
        self.efectos_disponibles = self.detectar_efectos()

        pygame.mixer.init()
        self.setup_ui()
        self.cargar_efectos()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        threading.Thread(target=self.voice_processor, daemon=True).start()
        
        # Iniciar Stage (Lienzo persistente)
        self.setup_stage()

    # ======================================================
    # STAGE PERSISTENTE Y SERVIDOR DE SEÑALES (UDP)
    # ======================================================
    def setup_stage(self):
        self.stage = tk.Toplevel(self.root)
        self.stage.title("Efectos - Stage")
        self.stage.attributes("-topmost", True)
        self.stage.attributes("-fullscreen", True)
        self.stage.config(bg="magenta")
        self.stage.attributes("-transparentcolor", "magenta")
        
        # Lienzo persistente único para efectos (boom, carta, rebote, etc.)
        self.persistent_canvas = tk.Canvas(self.stage, bg="magenta", highlightthickness=0, bd=0)
        self.persistent_canvas.pack(fill="both", expand=True)
        # Exponerlo para que los módulos de efectos lo encuentren
        self.stage.persistent_canvas = self.persistent_canvas
        
        # No dejar que el usuario la cierre directamente
        self.stage.protocol("WM_DELETE_WINDOW", lambda: None)
        # Ocultar de la barra de tareas si es posible (overrideredirect puede ser muy agresivo)
        # self.stage.overrideredirect(True) 
        

    # ======================================================
    # ESTILOS VISUALES PRO
    # ======================================================
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        bg_color = "#f0f0f0"
        card_bg = "#ffffff"
        text_fg = "#2c3e50"
        
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, font=("Segoe UI", 9), foreground=text_fg)
        self.style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), foreground=text_fg)
        self.style.configure("TCheckbutton", background=bg_color, font=("Segoe UI", 9))
        self.style.configure("TRadiobutton", background=bg_color, font=("Segoe UI", 9))
        
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=5, background="#e0e0e0")
        self.style.map("TButton", background=[("active", "#d0d0d0")])
        
        self.style.configure("TNotebook", background=bg_color, borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#e0e0e0", padding=[15, 8], font=("Segoe UI", 10))
        self.style.map("TNotebook.Tab", background=[("selected", "#ffffff")])
        
        self.style.configure("TLabelFrame", background=card_bg, foreground=text_fg, borderwidth=1, relief="solid")
        self.style.configure("TLabelFrame.Label", background="#eef2f5", foreground=text_fg, font=("Segoe UI", 10, "bold"))

    # ======================================================
    # UI SETUP
    # ======================================================
    def setup_ui(self):
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill="both", expand=True)
        self.create_tabs()

    def create_tabs(self):
        self.tab_control = self.create_scrollable_tab("Control")
        self.tab_config = self.create_scrollable_tab("Configuración")
        self.tab_efectos = self.create_scrollable_tab("Efectos")
        self.tab_comandos = self.create_scrollable_tab("Comandos")
        self.tab_workshop = ttk.Frame(self.notebook)
        self.tab_info = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_control, text=" 🎮 Control ")
        self.notebook.add(self.tab_config, text=" ⚙️ Ajustes ")
        self.notebook.add(self.tab_efectos, text=" 🎭 Efectos ")
        self.notebook.add(self.tab_comandos, text=" 💬 Comandos ")
        self.notebook.add(self.tab_workshop, text=" 🛠️ Workshop ")
        self.notebook.add(self.tab_info, text=" ℹ️ Info ")

        self.setup_control_tab()
        self.setup_config_tab()
        self.setup_efectos_tab()
        self.setup_comandos_tab()
        self.setup_workshop_tab()
        self.setup_info_tab()

    def create_scrollable_tab(self, name):
        return ttk.Frame(self.notebook)

    def setup_control_tab(self):
        parent = self.tab_control
        card = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        card.pack(fill="both", expand=True, padx=5, pady=5)
        
        inner = tk.Frame(card, bg="#ffffff")
        inner.pack(fill="both", expand=True, padx=15, pady=15)

        lbl_user = tk.Label(inner, text="Usuario de TikTok:", bg="#ffffff", font=("Segoe UI", 11, "bold"), fg="#2c3e50")
        lbl_user.pack(anchor="w", pady=(0, 5))
        
        self.ent_user = tk.Entry(inner, font=("Segoe UI", 10), bg="#f9f9f9", bd=1)
        self.ent_user.insert(0, self.config_data["usuario_tiktok"])
        self.ent_user.pack(fill="x", pady=(0, 15))

        frame_btns = tk.Frame(inner, bg="#ffffff")
        frame_btns.pack(pady=5)

        self.btn_toggle = ttk.Button(frame_btns, text="▶ INICIAR LIVE", command=self.toggle_bot, width=15)
        self.btn_toggle.pack(side="left", padx=5)

        self.btn_test = ttk.Button(frame_btns, text="🧪 PRE-VISUALIZADOR", command=self.toggle_test_mode, width=15)
        self.btn_test.pack(side="left", padx=5)

        lbl_log = tk.Label(inner, text="📜 Registro de Eventos:", bg="#ffffff", font=("Segoe UI", 11, "bold"), fg="#2c3e50")
        lbl_log.pack(anchor="w", pady=(15, 5))
        
        log_frame = tk.Frame(inner, bg="#1e1e1e", bd=1, relief="sunken")
        log_frame.pack(fill="both", expand=True)
        
        self.log_txt = tk.Text(log_frame, height=10, width=60, state='disabled', font=("Consolas", 9), bg="#1e1e1e", fg="#00ff00", insertbackground="white", bd=0)
        self.log_txt.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_config_tab(self):
        parent = self.tab_config
        canvas = tk.Canvas(parent, highlightthickness=0, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
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
        self.ent_msg_follow = ttk.Entry(frame_msg, width=50, font=("Segoe UI", 9))
        self.ent_msg_follow.insert(0, self.config_data["msg_follow"])
        self.ent_msg_follow.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 10))

        ttk.Label(frame_msg, text="Mensaje Gift:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.ent_msg_gift = ttk.Entry(frame_msg, width=50, font=("Segoe UI", 9))
        self.ent_msg_gift.insert(0, self.config_data["msg_gift"])
        self.ent_msg_gift.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 10))

        ttk.Label(frame_msg, text="Delay (segundos):").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.delay_val = tk.DoubleVar(value=self.config_data["delay"])
        ttk.Spinbox(frame_msg, from_=0, to=10, increment=0.5, width=10, textvariable=self.delay_val).grid(row=4, column=1, sticky="e", padx=5, pady=2)
        
        self.skip_delay = tk.BooleanVar(value=self.config_data["skip_delay_priority"])
        ttk.Checkbutton(frame_msg, text="Priorizar Regalos/Follows (Saltar delay)", variable=self.skip_delay).grid(row=5, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # --- SECCIÓN 2: LECTURA DE VOZ ---
        frame_voice = ttk.LabelFrame(main_content, text=" Lectura de Voz (TTS) ")
        frame_voice.pack(fill="x", pady=10)

        grid_voice = ttk.Frame(frame_voice)
        grid_voice.pack(fill="x", padx=5, pady=5)
        
        ttk.Checkbutton(grid_voice, text="🔊 Leer Chat", variable=self.voice_chat).grid(row=0, column=0, sticky="w", padx=5)
        ttk.Checkbutton(grid_voice, text="🔊 Leer Seguidores", variable=self.voice_follow).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Checkbutton(grid_voice, text="🔊 Leer Regalos", variable=self.voice_gift).grid(row=1, column=0, sticky="w", padx=5)
        ttk.Checkbutton(grid_voice, text="😎 Leer Emojis", variable=self.read_emojis).grid(row=1, column=1, sticky="w", padx=5)

        # --- SECCIÓN 3: VOLUMEN ---
        frame_vol = ttk.LabelFrame(main_content, text=" Control de Volumen ")
        frame_vol.pack(fill="x", pady=5)

        ttk.Label(frame_vol, text="Volumen Voz (TTS):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.volume_tts_val = tk.IntVar(value=self.config_data["volume_tts"])
        vol_tts_scale = ttk.Scale(frame_vol, from_=0, to=100, orient="horizontal", variable=self.volume_tts_val)
        vol_tts_scale.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(frame_vol, text="Volumen Efectos:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.volume_effects_val = tk.IntVar(value=self.config_data["volume_effects"])
        vol_eff_scale = ttk.Scale(frame_vol, from_=0, to=100, orient="horizontal", variable=self.volume_effects_val)
        vol_eff_scale.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        frame_vol.columnconfigure(1, weight=1)

        # --- SECCIÓN 4: SISTEMA Y CONEXIÓN ---
        frame_sys = ttk.LabelFrame(main_content, text=" Sistema y Conexión ")
        frame_sys.pack(fill="x", pady=5)

        grid_sys = ttk.Frame(frame_sys)
        grid_sys.pack(fill="x", padx=5, pady=5)

        ttk.Checkbutton(grid_sys, text="🎬 Activar Efectos de Animación", variable=self.filters_enabled).grid(row=0, column=0, sticky="w", padx=5)
        ttk.Checkbutton(grid_sys, text="🔇 Silenciar Fondo al reproducir efectos", variable=self.allow_effects_mute).grid(row=1, column=0, sticky="w", padx=5)

        ttk.Label(grid_sys, text="Reconexión (seg):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.reconnect_interval = tk.IntVar(value=self.config_data["reconnect_interval"])
        ttk.Spinbox(grid_sys, from_=1, to=60, width=5, textvariable=self.reconnect_interval).grid(row=2, column=1, sticky="e", padx=5, pady=2)

        ttk.Label(grid_sys, text="Intentos máximos:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.reconnect_attempts = tk.IntVar(value=self.config_data["reconnect_attempts"])
        ttk.Spinbox(grid_sys, from_=1, to=100, width=5, textvariable=self.reconnect_attempts).grid(row=3, column=1, sticky="e", padx=5, pady=2)

        # --- SECCIÓN 5: OPTIMIZACIÓN Y SLOTS ---
        frame_slots = ttk.LabelFrame(main_content, text=" Optimización y Superposición (Slots) ")
        frame_slots.pack(fill="x", pady=5)

        grid_slots = ttk.Frame(frame_slots)
        grid_slots.pack(fill="x", padx=5, pady=5)

        ttk.Label(grid_slots, text="Máx. Efectos Simultáneos (por tipo):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(grid_slots, from_=1, to=10, width=5, textvariable=self.max_concurrency).grid(row=0, column=1, sticky="e", padx=5, pady=2)

        ttk.Label(grid_slots, text="Retraso en Combo Escalera (seg):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(grid_slots, from_=0.1, to=5.0, increment=0.1, width=5, textvariable=self.delay_combo).grid(row=1, column=1, sticky="e", padx=5, pady=2)

    def setup_efectos_tab(self):
        parent = self.tab_efectos
        parent.config(padding="10")

        # Marco para los botones de acción superior
        frame_actions = ttk.Frame(parent)
        frame_actions.pack(fill="x", pady=5)

        self.btn_add_efecto = ttk.Button(frame_actions, text="[ + ] AGREGAR EFECTO", command=self.agregar_efecto_slot)
        self.btn_add_efecto.pack(side="left", padx=5)
        
        # 👇 NUEVO BOTÓN DE RECARGA
        self.btn_reload_efectos = ttk.Button(frame_actions, text="🔄 RECARGAR LISTA", command=self.recargar_efectos)
        self.btn_reload_efectos.pack(side="left", padx=5)

        self.canvas_efectos = tk.Canvas(parent, highlightthickness=0, bg="#f0f0f0")
        self.scrollbar_efectos = ttk.Scrollbar(parent, orient="vertical", command=self.canvas_efectos.yview)
        self.frame_efectos = ttk.Frame(self.canvas_efectos)

        self.frame_efectos.bind("<Configure>", lambda e: self.canvas_efectos.configure(scrollregion=self.canvas_efectos.bbox("all")))
        self.canvas_efectos.create_window((0, 0), window=self.frame_efectos, anchor="nw")
        self.canvas_efectos.configure(yscrollcommand=self.scrollbar_efectos.set)

        self.canvas_efectos.pack(side="left", fill="both", expand=True)
        self.scrollbar_efectos.pack(side="right", fill="y")
        self.frame_efectos.bind("<Configure>", self.toggle_scroll_efectos)

        if not self.efectos_disponibles:
            ttk.Label(parent, text="⚠️ No se encontraron efectos en gift_anim.py", foreground="#c0392b", font=("Segoe UI", 10, "bold")).pack(pady=20)

    def toggle_scroll_efectos(self, event=None):
        if self.frame_efectos.winfo_reqheight() > self.canvas_efectos.winfo_height():
            self.scrollbar_efectos.pack(side="right", fill="y")
        else:
            self.scrollbar_efectos.pack_forget()

    def setup_comandos_tab(self):
        parent = self.tab_comandos
        parent.config(padding="15")
        
        # --- Cabecera: Añadir Comando ---
        frame_add = ttk.LabelFrame(parent, text=" Nuevo Comando ")
        frame_add.pack(fill="x", pady=(0, 15))
        
        inner_add = ttk.Frame(frame_add)
        inner_add.pack(padx=10, pady=10, fill="x")
        
        ttk.Label(inner_add, text="!", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.ent_new_cmd = ttk.Entry(inner_add, font=("Segoe UI", 11))
        self.ent_new_cmd.pack(side="left", padx=5, fill="x", expand=True)
        self.ent_new_cmd.bind("<Return>", lambda e: self.agregar_comando())
        
        btn_add = ttk.Button(inner_add, text="Añadir Comando", command=self.agregar_comando)
        btn_add.pack(side="left", padx=5)

        # --- Lista de Comandos ---
        lbl_list = ttk.Label(parent, text="Comandos Activos:", font=("Segoe UI", 10, "bold"))
        lbl_list.pack(anchor="w", pady=(0, 5))
        
        self.frame_cmds_list = ttk.Frame(parent)
        self.frame_cmds_list.pack(fill="both", expand=True)
        
        self.actualizar_vista_comandos()

    def agregar_comando(self):
        cmd = self.ent_new_cmd.get().strip()
        if not cmd: return
        
        # Asegurar prefijo !
        full_cmd = f"!{cmd}" if not cmd.startswith("!") else cmd
        
        if full_cmd not in self.config_data["comandos"]:
            self.config_data["comandos"].append(full_cmd)
            self.ent_new_cmd.delete(0, tk.END)
            self.actualizar_vista_comandos()
            self.guardar_configuracion_actual()
            self.log(f"[Sistema] Comando añadido: {full_cmd}")
            # Actualizar dropdowns en Efectos
            self.recargar_listas_eventos()
        else:
            messagebox.showwarning("Comando Duplicado", f"El comando {full_cmd} ya existe.")

    def eliminar_comando(self, cmd):
        if cmd in self.config_data["comandos"]:
            self.config_data["comandos"].remove(cmd)
            self.actualizar_vista_comandos()
            self.guardar_configuracion_actual()
            self.log(f"[Sistema] Comando eliminado: {cmd}")
            self.recargar_listas_eventos()

    def actualizar_vista_comandos(self):
        # Limpiar frame
        for widget in self.frame_cmds_list.winfo_children():
            widget.destroy()
            
        # Layout tipo "wrap" manual o simple grid
        r, c = 0, 0
        for cmd in self.config_data["comandos"]:
            slot = tk.Frame(self.frame_cmds_list, bg="#eef2f5", bd=1, relief="solid", padx=5, pady=2)
            slot.grid(row=r, column=c, padx=5, pady=5, sticky="w")
            
            lbl = tk.Label(slot, text=cmd, bg="#eef2f5", font=("Segoe UI", 10, "bold"))
            lbl.pack(side="left")
            ToolTip(lbl).update_text(cmd) # Tooltip para el comando en la lista
            
            btn_del = tk.Button(slot, text="X", bg="#eef2f5", fg="red", bd=0, font=("Segoe UI", 9, "bold"),
                                command=lambda cmd=cmd: self.eliminar_comando(cmd))
            btn_del.pack(side="left", padx=(5, 0))
            ToolTip(btn_del).update_text(f"Eliminar comando {cmd}")
            
            c += 1
            if c > 3: # 4 por fila
                c = 0
                r += 1

    def recargar_listas_eventos(self):
        """Actualiza los Combobox de la pestaña Efectos para incluir nuevos comandos."""
        valores_eventos = ["follow", "all-gift"] + self.config_data["eventos"] + self.config_data["comandos"]
        for slot in self.efectos_slots:
            try:
                combo = slot.get("combo_evento")
                if combo:
                    valor_actual = combo.get()
                    combo['values'] = valores_eventos
                    # Sincronizar ToolTip
                    if "tt_evento" in slot:
                        slot["tt_evento"].update_text(valor_actual)
            except: pass

    def setup_workshop_tab(self):
        self.workshop_manager = WorkshopManager(self.tab_workshop, self)

    def setup_info_tab(self):
        parent = self.tab_info
        parent.config(padding="20")
        
        title = ttk.Label(parent, text="ℹ️ TikTok Live Bot - Pro", style="Header.TLabel")
        title.pack(anchor="w", pady=(0, 20))
        
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill="x")

        def add_section(title, body):
            section = ttk.LabelFrame(content_frame, text=f" {title} ")
            section.pack(fill="x", pady=(0, 15))
            lbl = ttk.Label(section, text=body, font=("Segoe UI", 10), wraplength=500, justify="left")
            lbl.pack(anchor="w", padx=10, pady=10)

        add_section("• Muteo Inteligente", "Usa la opción global 'Permitir que los efectos silencien el fondo' para activar el sistema. Luego, marca el icono 🔇 en cada filtro específico que deba cortar el sonido del juego o música.")
        add_section("• Gestión de Efectos", "Si agregas nuevos sonidos o efectos a las carpetas, usa el botón 'RECARGAR EFECTOS' para actualizar la lista sin reiniciar el programa.")

    # ======================================================
    # LÓGICA DE MUTEO
    # ======================================================
    def smart_mute_system_audio(self, exclude_pids=None):
        if not HAS_PYCAW:
            self.log("[Muteo] ERROR: PyCAW no disponible.")
            return False
        
        self.muted_sessions = []

        try:
            oledll.ole32.CoInitialize(None)
            time.sleep(0.3)
            sessions = AudioUtilities.GetAllSessions()
            
            count_muted = 0
            count_skipped = 0

            for session in sessions:
                try:
                    if not session.Process: continue
                    proc_name = session.Process.name().lower()
                    proc_pid = session.Process.pid

                    if "python" in proc_name:
                        count_skipped += 1
                        continue

                    volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                    try: current_mute = volume.GetMute()
                    except: current_mute = False

                    if not current_mute:
                        volume.SetMute(1, None)
                        self.muted_sessions.append(volume)
                        self.log(f"[Muteo 🔇] {proc_name}")
                        count_muted += 1
                except: pass

            if count_muted > 0:
                self.log(f"[Sistema] Silenciadas {count_muted} apps.")
            else:
                self.log("[Sistema] No se encontraron apps de fondo activas.")
            return True

        except Exception as e:
            self.log(f"[Muteo] Error: {e}")
            return False

    def unmute_system_audio(self):
        if not HAS_PYCAW: return
        try:
            if hasattr(self, 'muted_sessions'):
                self.log("[Audio] Restaurando sonidos...")
                for volume in self.muted_sessions:
                    try: volume.SetMute(0, None)
                    except: pass
                self.muted_sessions = []
        except: pass

    # ======================================================
    # EJECUCIÓN DE FILTROS
    # ======================================================
    def ejecutar_filtro(self, filtro, duracion, repeticiones=1, apply_mute=False, sub_tipo="NULL"):
        """Lanza el efecto en un hilo separado para no bloquear la interfaz."""
        thread = threading.Thread(
            target=self._ejecutar_filtro_thread,
            args=(filtro, duracion, repeticiones, apply_mute, sub_tipo),
            daemon=True
        )
        thread.start()

    def _ejecutar_filtro_thread(self, filtro, duracion, repeticiones, apply_mute, sub_tipo):
        if not os.path.exists("core/gift_anim.py"): return
        
        repeticiones = int(repeticiones)
        if str(duracion).isdigit(): dur = int(duracion)
        else: dur = 15
            
        volumen = self.volume_effects_val.get()
        should_mute = self.allow_effects_mute.get() and apply_mute
        exclude_pids = [os.getpid()]

        # Semáforo para este tipo de efecto
        if filtro not in self.semaphores:
            self.semaphores[filtro] = threading.Semaphore(self.max_concurrency.get())
        
        sem = self.semaphores[filtro]
        delay_escalera = self.delay_combo.get()

        for i in range(repeticiones):
            # El semáforo limita cuántos corren a la vez
            sem.acquire()
            
            # Lanzamos la ejecución real en otro hilo para que el sem.release sea gestionado
            # sin bloquear el bucle de "escalera"
            threading.Thread(
                target=self._lanzar_instancia_efecto,
                args=(filtro, dur, volumen, sub_tipo, sem, should_mute, exclude_pids),
                daemon=True
            ).start()

            # Efecto escalera: esperar n segundos antes de intentar lanzar el siguiente del combo
            if i < repeticiones - 1:
                time.sleep(delay_escalera)

    def _lanzar_instancia_efecto(self, filtro, dur, volumen, sub_tipo, sem, apply_mute, exclude_pids):
        try:
            if apply_mute:
                self.smart_mute_system_audio(exclude_pids=exclude_pids)

            # Identificar el módulo real y el sub_tipo
            if filtro.startswith("song_"):
                real_mod = "sonidoR"
                real_sub_tipo = filtro
            elif filtro.startswith("video_"):
                real_mod = "videoR"
                real_sub_tipo = filtro
            else:
                real_mod = filtro
                real_sub_tipo = sub_tipo

            try:
                import importlib
                nombre_mod = f"effect.effect_{real_mod}"
                mod = importlib.import_module(nombre_mod)
                if hasattr(mod, "ejecutar"):
                    # LLAMADA BLOQUEANTE PARA EL SLOT
                    mod.ejecutar(dur * 1000, volumen, real_sub_tipo, 1, self.stage)
                else:
                    raise Exception("Módulo no tiene función ejecutar")
            except Exception as e:
                print(f"[Panel] Fallo ejecución directa ({real_mod}): {e}")
                subprocess.Popen(
                    [sys.executable, "core/gift_anim.py", filtro, real_sub_tipo, str(dur), str(volumen), "1"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                ).wait()

            if apply_mute:
                time.sleep(0.1)
                self.unmute_system_audio()
        except Exception as e:
            if apply_mute: self.unmute_system_audio()
            print(f"Error en instancia de filtro ({filtro}):", e)
        finally:
            sem.release()

    # ======================================================
    # MODO TEST
    # ======================================================
    def toggle_test_mode(self):
        if not self.is_testing:
            confirm = messagebox.askyesno("Modo Prueba", "¿Entrar en modo simulación?")
            if confirm: self.start_test_mode()
        else: self.stop_test_mode()

    def start_test_mode(self):
        self.is_testing = True
        self.is_running = True
        self.deshabilitar_configuracion()
        self.btn_test.config(text="DETENER TEST")
        self.btn_toggle.config(state="disabled")
        self.update_log(">>> MODO TEST INICIADO")
        self.open_test_window()

    def stop_test_mode(self):
        self.is_testing = False
        self.is_running = False
        if self.test_window:
            try: self.test_window.destroy()
            except: pass
            self.test_window = None
        self.clear_queue()
        self.habilitar_configuracion()
        self.btn_test.config(text="🧪 PRE-VISUALIZADOR")
        self.btn_toggle.config(state="normal")
        self.update_log(">>> MODO TEST DETENIDO")

    def open_test_window(self):
        if self.test_window: return
        self.test_window = tk.Toplevel(self.root)
        self.test_window.title("Panel de Simulación")
        self.test_window.geometry("450x650")
        self.test_window.configure(bg="#f0f0f0")
        self.test_window.protocol("WM_DELETE_WINDOW", self.stop_test_mode)

        main_canvas = tk.Canvas(self.test_window, highlightthickness=0, bg="#f0f0f0")
        main_scrollbar = ttk.Scrollbar(self.test_window, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        frame_chat = ttk.LabelFrame(scrollable_frame, text=" Simular Chat ")
        frame_chat.pack(fill="x", padx=10, pady=5)

        grid_chat = ttk.Frame(frame_chat)
        grid_chat.pack(padx=5, pady=5)

        ttk.Label(grid_chat, text="Usuario:").grid(row=0, column=0, sticky="w")
        ent_test_user = ttk.Entry(grid_chat, width=20)
        ent_test_user.insert(0, "UsuarioTest")
        ent_test_user.grid(row=0, column=1, pady=2)

        ttk.Label(grid_chat, text="Mensaje:").grid(row=1, column=0, sticky="w")
        ent_test_msg = ttk.Entry(grid_chat, width=30)
        ent_test_msg.grid(row=1, column=1, pady=2)
        ent_test_msg.bind("<Return>", lambda e: self.sim_send_chat(ent_test_user, ent_test_msg))

        ttk.Button(grid_chat, text="Enviar", command=lambda: self.sim_send_chat(ent_test_user, ent_test_msg)).grid(row=2, column=0, columnspan=2, pady=5)

        frame_events = ttk.Frame(scrollable_frame)
        frame_events.pack(fill="x", padx=10, pady=5)
        ttk.Button(frame_events, text="👤 Simular Follow", command=lambda: self.add_to_queue("follow", ent_test_user.get(), None)).pack(side="left", expand=True, fill="x", padx=2)

        # SECCIÓN DE REGALOS CON COMBO
        frame_header_gifts = ttk.Frame(scrollable_frame)
        frame_header_gifts.pack(fill="x", padx=10, pady=(10, 5))
        
        ttk.Label(frame_header_gifts, text="🎁 Simular Regalos:", font=("Segoe UI", 10, "bold")).pack(side="left")
        
        ttk.Label(frame_header_gifts, text="Combo:").pack(side="left", padx=(20, 5))
        combo_cant = tk.IntVar(value=1)
        spin_combo = ttk.Spinbox(frame_header_gifts, from_=1, to=100, width=5, textvariable=combo_cant)
        spin_combo.pack(side="left")

        frame_gifts = ttk.Frame(scrollable_frame)
        frame_gifts.pack(fill="both", expand=True, padx=10, pady=5)

        # Obtener lista de regalos vinculados a efectos para resaltado
        regalos_con_efecto = set()
        for slot in self.efectos_slots:
            ev = slot["evento"].get().strip()
            if ev not in ("follow", "all-gift"):
                regalos_con_efecto.add(ev)

        eventos = self.config_data.get("eventos", [])
        col, row = 0, 0
        
        # Estilo para botones con filtro
        self.style.configure("LinkedGift.TButton", background="#d4edda") # Verde tenue

        for gift in eventos:
            # Si el regalo tiene efecto, usamos un estilo especial
            bg_btn = "#d4edda" if gift in regalos_con_efecto else "#f0f0f0"
            
            btn = tk.Button(frame_gifts, text=f"{gift}", width=12,
                bg=bg_btn, activebackground="#c3e6cb", bd=1, relief="raised",
                font=("Segoe UI", 9),
                command=lambda g=gift: self.add_to_queue("gift", ent_test_user.get(), None, {"gift": g, "cant": combo_cant.get()}))
            
            btn.grid(row=row, column=col, padx=2, pady=2)
            ToolTip(btn).update_text(f"Enviar regalo: {gift}")
            
            col += 1
            if col > 2: col, row = 0, row + 1
        scrollable_frame.update_idletasks()

    def sim_send_chat(self, entry_user, entry_msg):
        user = entry_user.get()
        msg = entry_msg.get()
        if msg:
            self.add_to_queue("comment", user, msg)
            entry_msg.delete(0, tk.END)

    # ======================================================
    # LÓGICA AUXILIAR
    # ======================================================
    def registrar_evento_gift(self, nombre_gift):
        if not nombre_gift or nombre_gift in ("follow", "all-gift"): return
        if nombre_gift not in self.config_data["eventos"]:
            self.config_data["eventos"].append(nombre_gift)
            self.config_data["eventos"].sort()
            self.guardar_configuracion_actual()

    def deshabilitar_configuracion(self):
        self.ent_user.config(state="disabled")
        if not self.is_testing: self.btn_test.config(state="disabled")
        # Deshabilitar configuración principal
        for child in self.tab_config.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Spinbox, ttk.Checkbutton, ttk.Scale)):
                try: child.config(state="disabled")
                except: pass
        
        # Deshabilitar controles de efectos (Botones de agregar/recargar/borrar)
        self.btn_add_efecto.config(state="disabled")
        if hasattr(self, 'btn_reload_efectos'):
            self.btn_reload_efectos.config(state="disabled")
            
        # Deshabilitar pestaña de comandos
        self.ent_new_cmd.config(state="disabled")
        for child in self.frame_cmds_list.winfo_children():
            # Deshabilitar botones X de los slots de comandos
            for sub in child.winfo_children():
                if isinstance(sub, tk.Button): sub.config(state="disabled")

        for frame in self.frame_efectos.winfo_children():
            if isinstance(frame, ttk.Frame):
                for widget in frame.winfo_children():
                    # Deshabilitar Combobox, Entries, Botones (Borrar) y Checkbuttons
                    if isinstance(widget, (ttk.Button, ttk.Combobox, ttk.Entry, ttk.Checkbutton)):
                        try: widget.config(state="disabled")
                        except: pass

    def habilitar_configuracion(self):
        self.ent_user.config(state="normal")
        self.btn_test.config(state="normal")
        # Habilitar configuración principal
        for child in self.tab_config.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Spinbox, ttk.Checkbutton, ttk.Scale)):
                try: child.config(state="normal")
                except: pass
        
        # Habilitar controles de efectos
        self.btn_add_efecto.config(state="normal")
        if hasattr(self, 'btn_reload_efectos'):
            self.btn_reload_efectos.config(state="normal")
            
        # Habilitar pestaña de comandos
        self.ent_new_cmd.config(state="normal")
        for child in self.frame_cmds_list.winfo_children():
            for sub in child.winfo_children():
                if isinstance(sub, tk.Button): sub.config(state="normal")

        for frame in self.frame_efectos.winfo_children():
            if isinstance(frame, ttk.Frame):
                for widget in frame.winfo_children():
                    if isinstance(widget, (ttk.Button, ttk.Combobox, ttk.Entry, ttk.Checkbutton)):
                        try:
                            # Los Combobox deben volver a 'readonly', no 'normal'
                            st = "readonly" if isinstance(widget, ttk.Combobox) else "normal"
                            widget.config(state=st)
                        except: pass

    def detectar_efectos(self):
        if not os.path.exists("core/gift_anim.py"): return []
        try:
            result = subprocess.run([sys.executable, "core/gift_anim.py", "--list-effects"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.strip().splitlines() if line.strip() and not line.startswith("pygame")]
        except: pass
        return []

    # 👇 NUEVA FUNCIÓN PARA RECARGAR EFECTOS
    def recargar_efectos(self):
        self.log("[Sistema] Recargando lista de efectos...")
        nuevos_efectos = self.detectar_efectos()
        
        if not nuevos_efectos:
            self.log("[Sistema] No se encontraron efectos en gift_anim.py")
            return
            
        self.efectos_disponibles = nuevos_efectos
        
        # Actualizar los dropdowns de los efectos existentes
        actualizados = 0
        for slot in self.efectos_slots:
            try:
                combo_widget = slot.get("combo_efecto")
                if combo_widget:
                    # Guardamos el valor actual
                    valor_actual = combo_widget.get()
                    # Actualizamos la lista de valores
                    combo_widget['values'] = self.efectos_disponibles
                    # Si el valor actual sigue existiendo, lo dejamos, si no, se queda el viejo visualmente pero es responsabilidad del usuario
                    # O podríamos forzar al primero si no está:
                    if valor_actual not in self.efectos_disponibles:
                        combo_widget.current(0)
                    # Sincronizar ToolTip
                    if "tt_efecto" in slot:
                        slot["tt_efecto"].update_text(combo_widget.get())
                    actualizados += 1
            except Exception as e:
                print(f"Error actualizando efecto: {e}")
                
        self.log(f"[Sistema] Se detectaron {len(self.efectos_disponibles)} efectos disponibles y se actualizaron {actualizados} efectos.")

    def agregar_efecto_slot(self, ev_val="follow", filtro_val=None, duracion_val="5", mute_val=False):
        if not self.efectos_disponibles: return
        fila = ttk.Frame(self.frame_efectos)
        fila.pack(fill="x", pady=2)
        
        evento = tk.StringVar(value=ev_val)
        filtro = tk.StringVar(value=filtro_val or self.efectos_disponibles[0])
        duracion = tk.StringVar(value=duracion_val)
        mute_var = tk.BooleanVar(value=mute_val)
        
        valores_eventos = ["follow", "all-gift"] + self.config_data["eventos"] + self.config_data.get("comandos", [])

        cb_evento = ttk.Combobox(fila, values=valores_eventos, width=12, textvariable=evento, state="readonly")
        cb_evento.pack(side="left", padx=2)
        ttk.Label(fila, text="➔").pack(side="left")
        
        # Tooltip para Evento
        tt_evento = ToolTip(cb_evento)
        tt_evento.update_text(evento.get())
        cb_evento.bind("<<ComboboxSelected>>", lambda e, tt=tt_evento, v=evento: tt.update_text(v.get()))

        # Guardamos referencia del widget para poder actualizarlo al recargar
        combo_efecto = ttk.Combobox(fila, values=self.efectos_disponibles, width=10, textvariable=filtro, state="readonly")
        combo_efecto.pack(side="left", padx=2)
        
        # Tooltip para Efecto
        tt_efecto = ToolTip(combo_efecto)
        tt_efecto.update_text(filtro.get())
        combo_efecto.bind("<<ComboboxSelected>>", lambda e, tt=tt_efecto, v=filtro: tt.update_text(v.get()))
        
        ttk.Label(fila, text="durante").pack(side="left")
        dur_entry = ttk.Entry(fila, width=4, textvariable=duracion)
        dur_entry.pack(side="left")
        ttk.Label(fila, text="s").pack(side="left")
        
        chk_mute_fondo = ttk.Checkbutton(fila, text="🔇", variable=mute_var)
        chk_mute_fondo.pack(side="left", padx=5)

        slot_ref = {
            "evento": evento, "filtro": filtro, "duracion": duracion, 
            "combo_efecto": combo_efecto, "combo_evento": cb_evento,
            "tt_efecto": tt_efecto, "tt_evento": tt_evento,
            "mute_var": mute_var, 
            "fila": fila, "dur_entry": dur_entry
        }
        self.efectos_slots.append(slot_ref)
        ttk.Button(fila, text="❌", width=3, command=lambda s=slot_ref: self.eliminar_efecto_slot(s)).pack(side="right", padx=(10, 0))
        self.root.after(10, self.toggle_scroll_efectos)

    def eliminar_efecto_slot(self, slot_a_eliminar):
        # Comprobar si está corriendo antes de eliminar (doble seguridad)
        if self.is_running:
            return 
            
        if slot_a_eliminar in self.efectos_slots:
            self.efectos_slots.remove(slot_a_eliminar)
            slot_a_eliminar["fila"].destroy()
            self.guardar_configuracion_actual()
            self.root.after(10, self.toggle_scroll_efectos)

    def validar_efectos(self):
        errores = []
        for slot in self.efectos_slots:
            filtro = slot["filtro"].get()
            duracion_str = slot["duracion"].get()
            if filtro not in self.efectos_disponibles: continue
            if not duracion_str.isdigit():
                errores.append(f"Duración inválida para '{filtro}': '{duracion_str}'")
                continue
            duracion = int(duracion_str)
            if filtro in ("rebote", "boom") and duracion == 0:
                errores.append(f"{filtro} = \"valor inválido, mínimo 1\"")
        return errores

    def mostrar_error_validacion(self, errores):
        error_win = tk.Toplevel(self.root)
        error_win.title("⚠️ Error de Validación")
        error_win.geometry("400x200")
        error_win.resizable(False, False)
        error_win.transient(self.root)
        error_win.grab_set()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        error_win.geometry(f"+{x}+{y}")
        ttk.Label(error_win, text="Se declaró un conflicto:\n" + "\n".join(errores), wraplength=380, justify="center").pack(pady=20)
        ttk.Button(error_win, text="Aceptar", command=error_win.destroy).pack(pady=10)

    def mostrar_error_usuario(self, mensaje):
        if self.is_testing: return
        error_win = tk.Toplevel(self.root)
        error_win.title("❌ Error de Usuario")
        error_win.geometry("400x150")
        error_win.resizable(False, False)
        error_win.transient(self.root)
        error_win.grab_set()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        error_win.geometry(f"+{x}+{y}")
        ttk.Label(error_win, text=f"🚨 {mensaje}", justify="center", wraplength=380).pack(pady=20)
        def aceptar():
            self.is_running = False
            self.btn_toggle.config(text="▶ INICIAR LIVE")
            self.update_log(">>> BOT DETENIDO (usuario inválido)")
            self.habilitar_configuracion()
            error_win.destroy()
        ttk.Button(error_win, text="Aceptar", command=aceptar).pack(pady=10)

    def guardar_configuracion_actual(self):
        config_to_save = {k: v for k, v in self.config_data.items() if k != "eventos"}
        config_to_save.update({
            "usuario_tiktok": self.ent_user.get(), "delay": self.delay_val.get(),
            "skip_delay_priority": self.skip_delay.get(), "msg_follow": self.ent_msg_follow.get(),
            "msg_gift": self.ent_msg_gift.get(), "voice_chat": self.voice_chat.get(),
            "voice_follow": self.voice_follow.get(), "voice_gift": self.voice_gift.get(),
            "read_emojis": self.read_emojis.get(),
            "filters_enabled": self.filters_enabled.get(),
            "allow_effects_mute": self.allow_effects_mute.get(),
            "filtros": self.exportar_efectos(),
            "comandos": self.config_data.get("comandos", []),
            "reconnect_interval": self.reconnect_interval.get(),
            "reconnect_attempts": self.reconnect_attempts.get(),
            "volume_tts": self.volume_tts_val.get(), "volume_effects": self.volume_effects_val.get()
        })
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            self.save_persistent_data()
        except Exception as e: print("Error guardar config:", e)

    def exportar_efectos(self):
        efectos_validos = []
        for s in self.efectos_slots:
            filtro_nombre = s["filtro"].get()
            if filtro_nombre and filtro_nombre in self.efectos_disponibles:
                efectos_validos.append({
                    "evento": s["evento"].get(), 
                    "filtro": filtro_nombre, 
                    "duracion": s["duracion"].get(),
                    "mute_background": s["mute_var"].get()
                })
        return efectos_validos

    def cargar_efectos(self):
        for f in self.config_data.get("filtros", []):
            filtro_val = f.get("filtro")
            if filtro_val and filtro_val in self.efectos_disponibles:
                self.agregar_efecto_slot(
                    ev_val=f.get("evento", "follow"), 
                    filtro_val=filtro_val, 
                    duracion_val=f.get("duracion", "5"),
                    mute_val=f.get("mute_background", False)
                )

    # ======================================================
    # MANEJO DE AUDIO TTS Y EMOJIS
    # ======================================================
    EMOJI_PATTERN = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )

    def play_audio(self, text):
        if not self.is_running: return
        try:
            if not self.read_emojis.get():
                text = self.EMOJI_PATTERN.sub(r'', text)
            
            filename = f"tts_{int(time.time() * 1000)}.mp3"
            gTTS(text=text, lang='es').save(filename)
            pygame.mixer.music.load(filename)
            pygame.mixer.music.set_volume(self.volume_tts_val.get() / 100.0)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy(): time.sleep(0.05)
            pygame.mixer.music.unload()
            os.remove(filename)
        except Exception as e: print("Error TTS:", e)

    # ======================================================
    # VOICE PROCESSOR (LÓGICA CORREGIDA)
    # ======================================================
    def voice_processor(self):
        while True:
            ev_type, user, content, vars_dict = self.queue.get()
            if not self.is_running:
                self.queue.task_done()
                continue
            try:
                texto = None
                texto_tts = None
                is_priority = ev_type in ("follow", "gift")
                voice_allowed = False

                if ev_type == "comment":
                    if self.voice_chat.get():
                        texto = content.strip() if content else None
                        texto_tts = texto
                        if texto_tts and texto_tts.startswith("!"):
                            for cmd in self.config_data.get("comandos", []):
                                if texto_tts.startswith(cmd):
                                    texto_tts = texto_tts[len(cmd):].strip()
                                    break
                        voice_allowed = True
                elif ev_type == "follow":
                    if self.voice_follow.get():
                        template = self.ent_msg_follow.get().strip()
                        if template:
                            texto = template.format(user=user)
                            texto_tts = texto
                            voice_allowed = True
                elif ev_type == "gift":
                    nombre_gift = vars_dict.get("gift", "").strip()
                    cantidad = vars_dict.get("cant", 1)
                    self.registrar_evento_gift(nombre_gift)
                    if self.voice_gift.get():
                        template = self.ent_msg_gift.get().strip()
                        if template:
                            texto = template.format(user=vars_dict.get("user", user), gift=nombre_gift, cant=cantidad)
                            texto_tts = texto
                            voice_allowed = True

                if texto or (ev_type in ("follow", "gift")):
                    log_text = f"[{ev_type.upper()}] {user}"
                    if texto: log_text += f": {texto}"
                    self.root.after(0, self.update_log, log_text)

                if self.filters_enabled.get():
                    efectos_pendientes = []
                    for slot in self.efectos_slots:
                        ev = slot["evento"].get().strip()
                        if ev_type == "follow" and ev == "follow":
                            efectos_pendientes.append((slot["filtro"].get(), slot["duracion"].get(), 1, slot["mute_var"].get()))
                        elif ev_type == "gift":
                            nombre_regalo_evento = vars_dict.get("gift", "").strip()
                            if ev == "all-gift" or ev == nombre_regalo_evento:
                                cantidad = vars_dict.get("cant", 1)
                                efectos_pendientes.append((slot["filtro"].get(), slot["duracion"].get(), cantidad, slot["mute_var"].get()))
                        elif ev_type == "comment" and content:
                            msg_clean = content.strip()
                            if msg_clean.startswith("!"):
                                # Trigger si empieza por el comando (ej: !bola8 hola)
                                if ev == msg_clean or msg_clean.startswith(ev + " "):
                                    efectos_pendientes.append((slot["filtro"].get(), slot["duracion"].get(), 1, slot["mute_var"].get()))
                    
                    if efectos_pendientes:
                        for filtro, duracion, repeticiones, apply_mute in efectos_pendientes:
                            self.ejecutar_filtro(filtro, duracion, repeticiones, apply_mute=apply_mute)
                        
                        if texto_tts and voice_allowed:
                            time.sleep(1.0)
                            self.play_audio(texto_tts)
                    else:
                        if texto_tts and voice_allowed:
                            self.play_audio(texto_tts)
                else:
                    if texto_tts and voice_allowed:
                        self.play_audio(texto_tts)

                debe_aplicar_delay = True
                if is_priority and self.skip_delay.get(): debe_aplicar_delay = False
                if debe_aplicar_delay: time.sleep(self.delay_val.get())

                # ======================================================
                # LÓGICA DE LECTURA DEL ÚLTIMO COMENTARIO
                # ======================================================
                if self.queue.qsize() > 5:
                    priority = []
                    last_comment = None 
                    
                    while not self.queue.empty():
                        item = self.queue.get()
                        if item[0] in ("follow", "gift"):
                            priority.append(item)
                        else:
                            last_comment = item
                        self.queue.task_done()
                    
                    for p in priority: self.queue.put(p)
                    
                    if last_comment: 
                        self.queue.put(last_comment)
                        
            except Exception as e: 
                print("Error en voice_processor:", e)
                traceback.print_exc()
            self.queue.task_done()
            
    def update_log(self, text):
        self.log_txt.config(state='normal')
        self.log_txt.insert(tk.END, text + "\n")
        self.log_txt.see(tk.END)
        self.log_txt.config(state='disabled')

    def log(self, text):
        self.update_log(text)

    def toggle_bot(self):
        if self.is_testing: return
        if not self.is_running:
            errores = self.validar_efectos()
            if errores: self.mostrar_error_validacion(errores); return
            self.is_running = True
            self.btn_toggle.config(text="⏹ DETENER LIVE")
            self.btn_test.config(state="disabled")
            self.update_log(">>> CONECTANDO AL LIVE...")
            self.deshabilitar_configuracion()
            self.scraper = TikTokScraper(self.ent_user.get(), self.add_to_queue, error_callback=self.mostrar_error_usuario)
            self.scraper.max_reintentos = self.reconnect_attempts.get()
            self.scraper.intervalo_reintento = self.reconnect_interval.get()
            self.scraper_thread = threading.Thread(target=self.scraper.run, daemon=True)
            self.scraper_thread.start()
        else:
            self.is_running = False
            self.btn_toggle.config(text="▶ INICIAR LIVE")
            self.btn_test.config(state="normal")
            self.update_log(">>> BOT DETENIDO")
            self.habilitar_configuracion()
            if hasattr(self, "scraper"): self.scraper.stop()
            self.clear_queue()

    def add_to_queue(self, ev_type, user, content, vars_dict=None):
        if self.is_running: self.queue.put((ev_type, user, content, vars_dict or {}))

    def clear_queue(self):
        while not self.queue.empty():
            try: self.queue.get_nowait(); self.queue.task_done()
            except: break

    def load_config(self):
        os.makedirs("core/profile", exist_ok=True)
        os.makedirs("core", exist_ok=True)
        self.load_persistent_data()
        if not os.path.exists(self.config_file):
            try:
                with open(self.config_file, "w", encoding="utf-8") as f:
                    config_sin_eventos = {k: v for k, v in self.config_data.items() if k != "eventos"}
                    json.dump(config_sin_eventos, f, indent=4, ensure_ascii=False)
            except: pass
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for key, value in loaded.items():
                        if key not in ("eventos", "comandos"): self.config_data[key] = value
                    self.config_data["allow_effects_mute"] = loaded.get("allow_effects_mute", True)
                    self.config_data["read_emojis"] = loaded.get("read_emojis", True)
                    self.config_data["comandos"] = loaded.get("comandos", ["!bola8"])
            except: pass

    def load_persistent_data(self):
        if not os.path.exists(self.data_file):
            try:
                datos_por_defecto = {"eventos": ["2026", "Blue Heart", "Cake Slice", "Cap", "Capybara", "Doughnut", "Elephant trunk", "Finger Heart", "Flame Heart GDM", "GG", "Glow Stick", "Graduation Bouquet", "Hat and Mustache", "Heart", "Heart Me", "Heart Puff", "Hearts", "I'm Ready", "Ice Cream Cone", "Love you so much", "Maracas", "Popular Vote", "Rosa", "Rose", "Squirrel", "TGIF", "Team Cheers", "TikTok", "Wave Firework", "White Rose", "Woodland Wonder", "You're awesome"]}
                with open(self.data_file, "w", encoding="utf-8") as f: json.dump(datos_por_defecto, f, indent=4, ensure_ascii=False)
            except: return
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.config_data["eventos"] = data.get("eventos", ["Doughnut"])
        except: self.config_data["eventos"] = ["Doughnut"]

    def save_persistent_data(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({"eventos": self.config_data["eventos"]}, f, indent=4, ensure_ascii=False)
        except: pass

    def on_closing(self):
        config_to_save = {k: v for k, v in self.config_data.items() if k != "eventos"}
        config_to_save.update({
            "usuario_tiktok": self.ent_user.get(), "delay": self.delay_val.get(),
            "skip_delay_priority": self.skip_delay.get(), "msg_follow": self.ent_msg_follow.get(),
            "msg_gift": self.ent_msg_gift.get(), "voice_chat": self.voice_chat.get(),
            "voice_follow": self.voice_follow.get(), "voice_gift": self.voice_gift.get(),
            "read_emojis": self.read_emojis.get(),
            "filters_enabled": self.filters_enabled.get(),
            "allow_effects_mute": self.allow_effects_mute.get(),
            "max_concurrency": self.max_concurrency.get(),
            "delay_combo": self.delay_combo.get(),
            "filtros": self.exportar_efectos(),
            "comandos": self.config_data.get("comandos", []),
            "reconnect_interval": self.reconnect_interval.get(),
            "reconnect_attempts": self.reconnect_attempts.get(),
            "volume_tts": self.volume_tts_val.get(), "volume_effects": self.volume_effects_val.get()
        })
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            self.save_persistent_data()
        except: pass
        self.root.destroy()