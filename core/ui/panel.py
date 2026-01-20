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
from tkinter import messagebox

# Importación del scraper
from content_tiktok import TikTokScraper

# ===== IMPORTACIÓN OPCIONAL DE PYCAW =====
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume
    from comtypes import CLSCTX_ALL
    from ctypes import cast, POINTER, oledll
    import comtypes
    HAS_PYCAW = True
except Exception:
    HAS_PYCAW = False

class MainPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Live Bot - Pro")
        self.root.geometry("600x530")

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
            "filters_enabled": True,
            "allow_effects_mute": True,  # 👈 NUEVA OPCIÓN GLOBAL
            "filtros": [],
            "eventos": ["Doughnut"],
            "reconnect_interval": 5,
            "reconnect_attempts": 10,
            "volume_tts": 100,
            "volume_effects": 100
        }

        self.load_config()

        # Variables Tkinter
        self.voice_chat = tk.BooleanVar(value=self.config_data["voice_chat"])
        self.voice_follow = tk.BooleanVar(value=self.config_data["voice_follow"])
        self.voice_gift = tk.BooleanVar(value=self.config_data["voice_gift"])
        self.filters_enabled = tk.BooleanVar(value=self.config_data["filters_enabled"])
        # Usamos una variable global para el switch principal, y lógica interna para filtros
        self.allow_effects_mute = tk.BooleanVar(value=self.config_data.get("allow_effects_mute", True))

        # Filtros y UI
        self.filtros_slots = []
        self.filtros_disponibles = self.detectar_filtros()

        pygame.mixer.init()
        self.setup_ui()
        self.cargar_filtros()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        threading.Thread(target=self.voice_processor, daemon=True).start()

    # ======================================================
    # UI SETUP
    # ======================================================
    def setup_ui(self):
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_tabs()

    def create_tabs(self):
        self.tab_control = self.create_scrollable_tab("Control")
        self.tab_config = self.create_scrollable_tab("Config")
        self.tab_filtros = self.create_scrollable_tab("Filtros")
        self.tab_info = self.create_scrollable_tab("Info")

        self.notebook.add(self.tab_control, text="Control")
        self.notebook.add(self.tab_config, text="Config")
        self.notebook.add(self.tab_filtros, text="Filtros")
        self.notebook.add(self.tab_info, text="Info")

        self.setup_control_tab()
        self.setup_config_tab()
        self.setup_filtros_tab()
        self.setup_info_tab()

    def create_scrollable_tab(self, name):
        return ttk.Frame(self.notebook)

    def setup_control_tab(self):
        parent = self.tab_control
        parent.config(padding="20")

        ttk.Label(parent, text="Usuario de TikTok:").pack(anchor="w")
        self.ent_user = ttk.Entry(parent, width=50)
        self.ent_user.insert(0, self.config_data["usuario_tiktok"])
        self.ent_user.pack(pady=5)

        frame_btns = ttk.Frame(parent)
        frame_btns.pack(pady=10)

        self.btn_toggle = ttk.Button(frame_btns, text="Iniciar Live", command=self.toggle_bot)
        self.btn_toggle.pack(side="left", padx=5)

        self.btn_test = ttk.Button(frame_btns, text="Pre-visualizador", command=self.toggle_test_mode)
        self.btn_test.pack(side="left", padx=5)

        self.log_txt = tk.Text(parent, height=10, width=60, state='disabled', font=("Segoe UI", 9))
        self.log_txt.pack(pady=10, fill="x")

    def setup_config_tab(self):
        parent = self.tab_config
        parent.config(padding="20")

        ttk.Label(parent, text="Delay (seg):").grid(row=0, column=0, sticky="w", pady=2)
        self.delay_val = tk.DoubleVar(value=self.config_data["delay"])
        ttk.Spinbox(parent, from_=0, to=10, increment=0.5, width=8, textvariable=self.delay_val).grid(row=0, column=1, pady=2)

        self.skip_delay = tk.BooleanVar(value=self.config_data["skip_delay_priority"])
        ttk.Checkbutton(parent, text="Prioridad Regalos / Follows", variable=self.skip_delay).grid(row=1, column=0, columnspan=2, sticky="w", pady=2)

        ttk.Label(parent, text="Msg Follow:").grid(row=2, column=0, sticky="w", pady=2)
        self.ent_msg_follow = ttk.Entry(parent, width=40)
        self.ent_msg_follow.insert(0, self.config_data["msg_follow"])
        self.ent_msg_follow.grid(row=3, column=0, columnspan=2, pady=2)

        ttk.Label(parent, text="Msg Gift:").grid(row=4, column=0, sticky="w", pady=2)
        self.ent_msg_gift = ttk.Entry(parent, width=40)
        self.ent_msg_gift.insert(0, self.config_data["msg_gift"])
        self.ent_msg_gift.grid(row=5, column=0, columnspan=2, pady=2)

        ttk.Separator(parent, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Checkbutton(parent, text="🔊 Leer CHAT", variable=self.voice_chat).grid(row=7, column=0, sticky="w", pady=2)
        ttk.Checkbutton(parent, text="🔊 Leer FOLLOW", variable=self.voice_follow).grid(row=8, column=0, sticky="w", pady=2)
        ttk.Checkbutton(parent, text="🔊 Leer GIFT", variable=self.voice_gift).grid(row=9, column=0, sticky="w", pady=2)
        ttk.Checkbutton(parent, text="🎬 Activar FILTROS", variable=self.filters_enabled).grid(row=10, column=0, sticky="w", pady=2)
        
        # 👇 NUEVA OPCIÓN GLOBAL CONTROLADA
        chk_mute_global = ttk.Checkbutton(parent, text="🔇 Permitir que los efectos silencien el fondo", variable=self.allow_effects_mute)
        chk_mute_global.grid(row=11, column=0, columnspan=2, sticky="w", pady=2)
        
        ttk.Separator(parent, orient="horizontal").grid(row=12, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(parent, text="Reconexión (seg):").grid(row=13, column=0, sticky="w", pady=2)
        self.reconnect_interval = tk.IntVar(value=self.config_data["reconnect_interval"])
        ttk.Spinbox(parent, from_=1, to=60, width=8, textvariable=self.reconnect_interval).grid(row=13, column=1, pady=2)

        ttk.Label(parent, text="Intentos máximos:").grid(row=14, column=0, sticky="w", pady=2)
        self.reconnect_attempts = tk.IntVar(value=self.config_data["reconnect_attempts"])
        ttk.Spinbox(parent, from_=1, to=100, width=8, textvariable=self.reconnect_attempts).grid(row=14, column=1, pady=2)

        ttk.Separator(parent, orient="horizontal").grid(row=15, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(parent, text="Volumen TTS (%):").grid(row=16, column=0, sticky="w", pady=2)
        self.volume_tts_val = tk.IntVar(value=self.config_data["volume_tts"])
        ttk.Spinbox(parent, from_=0, to=100, width=6, textvariable=self.volume_tts_val).grid(row=16, column=1, pady=2, sticky="w")
        self.volume_tts_slider = ttk.Scale(parent, from_=0, to=100, orient="horizontal", variable=self.volume_tts_val, length=150)
        self.volume_tts_slider.grid(row=17, column=1, pady=2, sticky="w")

        ttk.Label(parent, text="Volumen efectos (%):").grid(row=18, column=0, sticky="w", pady=2)
        self.volume_effects_val = tk.IntVar(value=self.config_data["volume_effects"])
        ttk.Spinbox(parent, from_=0, to=100, width=6, textvariable=self.volume_effects_val).grid(row=18, column=1, pady=2, sticky="w")
        self.volume_effects_slider = ttk.Scale(parent, from_=0, to=100, orient="horizontal", variable=self.volume_effects_val, length=150)
        self.volume_effects_slider.grid(row=19, column=1, pady=2, sticky="w")

    def setup_filtros_tab(self):
        parent = self.tab_filtros
        parent.config(padding="10")

        self.btn_add_filtro = ttk.Button(parent, text="[ + ] Agregar Filtro", command=self.agregar_filtro_slot)
        self.btn_add_filtro.pack(anchor="w", pady=5)

        self.canvas_filtros = tk.Canvas(parent, highlightthickness=0)
        self.scrollbar_filtros = ttk.Scrollbar(parent, orient="vertical", command=self.canvas_filtros.yview)
        self.frame_filtros = ttk.Frame(self.canvas_filtros)

        self.frame_filtros.bind("<Configure>", lambda e: self.canvas_filtros.configure(scrollregion=self.canvas_filtros.bbox("all")))
        self.canvas_filtros.create_window((0, 0), window=self.frame_filtros, anchor="nw")
        self.canvas_filtros.configure(yscrollcommand=self.scrollbar_filtros.set)

        self.canvas_filtros.pack(side="left", fill="both", expand=True)
        self.scrollbar_filtros.pack(side="right", fill="y")
        self.frame_filtros.bind("<Configure>", self.toggle_scroll_filtros)

        if not self.filtros_disponibles:
            ttk.Label(parent, text="⚠️ No se encontraron efectos en gift_anim.py", foreground="red").pack(pady=5)

    def toggle_scroll_filtros(self, event=None):
        if self.frame_filtros.winfo_reqheight() > self.canvas_filtros.winfo_height():
            self.scrollbar_filtros.pack(side="right", fill="y")
        else:
            self.scrollbar_filtros.pack_forget()

    def setup_info_tab(self):
        parent = self.tab_info
        parent.config(padding="20")
        title = ttk.Label(parent, text="ℹ️ TikTok Live Bot - Pro", font=("Segoe UI", 14, "bold"), foreground="#2c3e50")
        title.pack(anchor="w", pady=(0, 15))
        
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill="x")

        def add_section(title, body):
            section = ttk.Frame(content_frame)
            section.pack(fill="x", pady=(0, 12))
            ttk.Label(section, text=title, font=("Segoe UI", 11, "bold"), foreground="#3498db").pack(anchor="w")
            ttk.Label(section, text=body, font=("Segoe UI", 10), wraplength=500, justify="left").pack(anchor="w", pady=(5, 0))

        add_section("• Muteo Inteligente", "Usa la opción global 'Permitir que los efectos silencien el fondo' para activar el sistema. Luego, marca el icono 🔇 en cada filtro específico que deba cortar el sonido del juego o música.")

    # ======================================================
    # LÓGICA DE MUTEO AGRESIVA (TODO TIPO DE CANALES)
    # ======================================================
    def smart_mute_system_audio(self, exclude_pids=None):
        """
        Estrategia: Muteo Total por Exclusión.
        Escanea TODOS los flujos de audio del dispositivo predeterminado 
        (Consola, Multimedia, Comunicaciones) y silencia cualquier sesión
        que NO sea python.exe.
        """
        if not HAS_PYCAW:
            self.log("[Muteo] ERROR: PyCAW no disponible.")
            return False
        
        self.muted_sessions = []

        try:
            oledll.ole32.CoInitialize(None)
            
            # Pausa para estabilización de audio
            time.sleep(0.3)
            
            # NOTA: GetSpeakers() devuelve el dispositivo predeterminado.
            # GetSessions() en este contexto debería traer las sesiones activas en él.
            # En versiones recientes de pycaw, esto abarca la mayoría de casos.
            sessions = AudioUtilities.GetAllSessions()
            
            count_muted = 0
            count_skipped = 0

            for session in sessions:
                try:
                    # 1. Verificamos si tiene proceso asociado
                    if not session.Process:
                        # A veces son sonidos del sistema "huérfanos". 
                        # Si quieres silenciar también sonidos del sistema de Windows (notificaciones, beeps),
                        # puedes quitar el 'continue' de abajo. Pero es peligroso si pierdes la referencia.
                        # Por seguridad, ignoramos sesiones sin proceso conocido.
                        continue

                    proc_name = session.Process.name().lower()
                    proc_pid = session.Process.pid

                    # 2. PROTECCIÓN TOTAL DE PYTHON
                    # Si el nombre contiene "python", NO lo tocamos.
                    if "python" in proc_name:
                        count_skipped += 1
                        continue

                    # 3. INTENTO DE MUTEO AGRESIVO
                    volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                    
                    # Verificamos estado actual
                    try:
                        current_mute = volume.GetMute()
                    except Exception:
                        current_mute = False # Asumir que no está muteado si falla la lectura

                    if not current_mute:
                        # Intentamos silenciar
                        volume.SetMute(1, None)
                        self.muted_sessions.append(volume)
                        self.log(f"[Muteo 🔇] {proc_name} (PID: {proc_pid})")
                        count_muted += 1

                except Exception as e:
                    # Ignoramos errores individuales para no detener el bucle completo
                    # (por ejemplo, si un proceso cierra justo en este milisegundo)
                    pass

            if count_muted > 0:
                self.log(f"[Sistema] Silenciadas {count_muted} apps. ({count_skipped} procesos Python protegidos).")
            else:
                self.log("[Sistema] No se encontraron aplicaciones de fondo activas para silenciar.")

            return True

        except Exception as e:
            self.log(f"[Muteo] Error General: {e}")
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
        except Exception as e:
            self.log("Error desmuteando:", e)

    # ======================================================
    # LÓGICA DE EJECUCIÓN DE FILTROS
    # ======================================================
    def ejecutar_filtro(self, filtro, duracion, repeticiones=1, apply_mute=False):
        if not os.path.exists("core/gift_anim.py"): return

        # Lista de PIDs a proteger (El bot + El efecto)
        exclude_pids = [os.getpid()]
        
        if duracion.isdigit(): dur = int(duracion)
        else: dur = 15
            
        volumen = self.volume_effects_val.get()
        
        # Solo si está activo globalmente Y en el filtro individual
        should_mute = self.allow_effects_mute.get() and apply_mute

        try:
            for i in range(repeticiones):
                proc = subprocess.Popen(
                    [sys.executable, "core/gift_anim.py", filtro, str(dur), str(volumen)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                effect_pid = proc.pid
                
                if should_mute and i == 0:
                    # Pasamos la lista completa (Bot + Efecto) para que no mutee el efecto
                    self.smart_mute_system_audio(exclude_pids=exclude_pids)

                proc.wait()
                if repeticiones > 1: time.sleep(0.1)
            
            if should_mute:
                time.sleep(0.2)
                self.unmute_system_audio()

        except Exception as e:
            if should_mute: self.unmute_system_audio()
            print("Error al ejecutar filtro:", e)

    # ======================================================
    # PRE-VISUALIZADOR
    # ======================================================
    def toggle_test_mode(self):
        if not self.is_testing:
            confirm = messagebox.askyesno("Modo Prueba", "¿Estás seguro de que quieres entrar en modo testing?\n\nEsto simulará un live usando la configuración actual.")
            if confirm: self.start_test_mode()
        else: self.stop_test_mode()

    def start_test_mode(self):
        self.is_testing = True
        self.is_running = True
        self.deshabilitar_configuracion()
        self.btn_test.config(text="Detener Test")
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
        self.btn_test.config(text="Pre-visualizador")
        self.btn_toggle.config(state="normal")
        self.update_log(">>> MODO TEST DETENIDO")

    def open_test_window(self):
        if self.test_window: return
        self.test_window = tk.Toplevel(self.root)
        self.test_window.title("Panel de Simulación")
        self.test_window.geometry("450x650")
        self.test_window.protocol("WM_DELETE_WINDOW", self.stop_test_mode)

        main_canvas = tk.Canvas(self.test_window, highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(self.test_window, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        frame_chat = ttk.LabelFrame(scrollable_frame, text="💬 Simular Chat", padding=10)
        frame_chat.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_chat, text="Usuario:").grid(row=0, column=0, sticky="w")
        ent_test_user = ttk.Entry(frame_chat, width=20)
        ent_test_user.insert(0, "UsuarioTest")
        ent_test_user.grid(row=0, column=1, pady=2)

        ttk.Label(frame_chat, text="Mensaje:").grid(row=1, column=0, sticky="w")
        ent_test_msg = ttk.Entry(frame_chat, width=30)
        ent_test_msg.grid(row=1, column=1, pady=2)
        ent_test_msg.bind("<Return>", lambda e: self.sim_send_chat(ent_test_user, ent_test_msg))

        ttk.Button(frame_chat, text="Enviar", command=lambda: self.sim_send_chat(ent_test_user, ent_test_msg)).grid(row=2, column=0, columnspan=2, pady=5)

        frame_events = ttk.Frame(scrollable_frame)
        frame_events.pack(fill="x", padx=10, pady=5)
        ttk.Button(frame_events, text="👤 Simular Follow", command=lambda: self.add_to_queue("follow", ent_test_user.get(), None)).pack(side="left", expand=True, fill="x", padx=2)

        ttk.Label(scrollable_frame, text="🎁 Simular Regalos:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

        frame_gifts = ttk.Frame(scrollable_frame)
        frame_gifts.pack(fill="both", expand=True, padx=10, pady=5)

        eventos = self.config_data.get("eventos", [])
        col, row = 0, 0
        for gift in eventos:
            btn = ttk.Button(frame_gifts, text=f"{gift}", width=15,
                command=lambda g=gift: self.add_to_queue("gift", ent_test_user.get(), None, {"gift": g, "cant": 1}))
            btn.grid(row=row, column=col, padx=2, pady=2)
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
    # LOGICA GENERAL Y AUXILIARES
    # ======================================================
    def registrar_evento_gift(self, nombre_gift):
        if not nombre_gift or nombre_gift in ("follow", "all-gift"): return
        if nombre_gift not in self.config_data["eventos"]:
            self.config_data["eventos"].append(nombre_gift)
            self.config_data["eventos"].sort()
            self.guardar_configuracion_actual()
            print(f"🆕 Nuevo regalo registrado: {nombre_gift}")

    def deshabilitar_configuracion(self):
        self.ent_user.config(state="disabled")
        if not self.is_testing: self.btn_test.config(state="disabled")
        for child in self.tab_config.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Spinbox, ttk.Checkbutton, ttk.Scale)):
                try: child.config(state="disabled")
                except: pass
        self.btn_add_filtro.config(state="disabled")
        for frame in self.frame_filtros.winfo_children():
            if isinstance(frame, ttk.Frame):
                for widget in frame.winfo_children():
                    if isinstance(widget, (ttk.Combobox, ttk.Entry)): widget.config(state="disabled")

    def habilitar_configuracion(self):
        self.ent_user.config(state="normal")
        self.btn_test.config(state="normal")
        for child in self.tab_config.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Spinbox, ttk.Checkbutton, ttk.Scale)):
                try: child.config(state="normal")
                except: pass
        self.btn_add_filtro.config(state="normal")
        for frame in self.frame_filtros.winfo_children():
            if isinstance(frame, ttk.Frame):
                for widget in frame.winfo_children():
                    if isinstance(widget, (ttk.Combobox, ttk.Entry)): widget.config(state="normal")

    def detectar_filtros(self):
        if not os.path.exists("core/gift_anim.py"): return []
        try:
            result = subprocess.run([sys.executable, "core/gift_anim.py", "--list-effects"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.strip().splitlines() if line.strip() and not line.startswith("pygame")]
        except: pass
        return []

    def agregar_filtro_slot(self, ev_val="follow", filtro_val=None, duracion_val="5", mute_val=False):
        if not self.filtros_disponibles: return
        fila = ttk.Frame(self.frame_filtros)
        fila.pack(fill="x", pady=2)
        
        evento = tk.StringVar(value=ev_val)
        filtro = tk.StringVar(value=filtro_val or self.filtros_disponibles[0])
        duracion = tk.StringVar(value=duracion_val)
        mute_var = tk.BooleanVar(value=mute_val) # 👈 Nueva variable individual
        
        valores_eventos = ["follow", "all-gift"] + self.config_data["eventos"]

        ttk.Combobox(fila, values=valores_eventos, width=12, textvariable=evento, state="readonly").pack(side="left", padx=2)
        ttk.Label(fila, text="hacer").pack(side="left")
        ttk.Combobox(fila, values=self.filtros_disponibles, width=10, textvariable=filtro, state="readonly").pack(side="left", padx=2)
        ttk.Label(fila, text="durante").pack(side="left")
        dur_entry = ttk.Entry(fila, width=4, textvariable=duracion)
        dur_entry.pack(side="left")
        ttk.Label(fila, text="s").pack(side="left")
        
        # 👇 NUEVO CHECKBOX PARA MUTEAR FONDO
        chk_mute_fondo = ttk.Checkbutton(fila, text="🔇", variable=mute_var)
        chk_mute_fondo.pack(side="left", padx=5)

        slot_ref = {
            "evento": evento, "filtro": filtro, "duracion": duracion, 
            "mute_var": mute_var, # Guardar referencia
            "fila": fila, "dur_entry": dur_entry
        }
        self.filtros_slots.append(slot_ref)
        ttk.Button(fila, text="❌", width=3, command=lambda s=slot_ref: self.eliminar_filtro_slot(s)).pack(side="right", padx=(10, 0))
        self.root.after(10, self.toggle_scroll_filtros)

    def eliminar_filtro_slot(self, slot_a_eliminar):
        if slot_a_eliminar in self.filtros_slots:
            self.filtros_slots.remove(slot_a_eliminar)
            slot_a_eliminar["fila"].destroy()
            self.guardar_configuracion_actual()
            self.root.after(10, self.toggle_scroll_filtros)

    def validar_filtros(self):
        errores = []
        for slot in self.filtros_slots:
            filtro = slot["filtro"].get()
            duracion_str = slot["duracion"].get()
            if filtro not in self.filtros_disponibles: continue
            if not duracion_str.isdigit():
                errores.append(f"Duración inválida para '{filtro}': '{duracion_str}' (debe ser número)")
                continue
            duracion = int(duracion_str)
            if filtro in ("rebote", "boom") and duracion == 0:
                errores.append(f"{filtro} = \"value invalid, minim is =>1\"")
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
        ttk.Label(error_win, text="Se declaró un conflicto:\n" + "\n".join(errores) + "\n\nPor favor consulte en 'Info'", wraplength=380, justify="center").pack(pady=20)
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
        ttk.Label(error_win, text=f"🚨 {mensaje}\n\n• Verifica que el usuario exista\n• Asegúrate de que esté en vivo", justify="center", wraplength=380).pack(pady=20)
        def aceptar():
            self.is_running = False
            self.btn_toggle.config(text="Iniciar Live")
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
            "filters_enabled": self.filters_enabled.get(),
            "allow_effects_mute": self.allow_effects_mute.get(),
            "filtros": self.exportar_filtros(), "reconnect_interval": self.reconnect_interval.get(),
            "reconnect_attempts": self.reconnect_attempts.get(),
            "volume_tts": self.volume_tts_val.get(), "volume_effects": self.volume_effects_val.get()
        })
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            self.save_persistent_data()
        except Exception as e: print("Error al guardar configuración:", e)

    def exportar_filtros(self):
        filtros_validos = []
        for s in self.filtros_slots:
            filtro_nombre = s["filtro"].get()
            if filtro_nombre and filtro_nombre in self.filtros_disponibles:
                # 👈 Exportamos también la variable de mute individual
                filtros_validos.append({
                    "evento": s["evento"].get(), 
                    "filtro": filtro_nombre, 
                    "duracion": s["duracion"].get(),
                    "mute_background": s["mute_var"].get()
                })
        return filtros_validos

    def cargar_filtros(self):
        for f in self.config_data.get("filtros", []):
            filtro_val = f.get("filtro")
            if filtro_val and filtro_val in self.filtros_disponibles:
                # 👈 Cargamos la variable de mute individual
                self.agregar_filtro_slot(
                    ev_val=f.get("evento", "follow"), 
                    filtro_val=filtro_val, 
                    duracion_val=f.get("duracion", "5"),
                    mute_val=f.get("mute_background", False)
                )

    def voice_processor(self):
        while True:
            ev_type, user, content, vars_dict = self.queue.get()
            if not self.is_running:
                self.queue.task_done()
                continue
            try:
                texto = None
                is_priority = ev_type in ("follow", "gift")
                voice_allowed = False

                if ev_type == "comment":
                    if self.voice_chat.get():
                        texto = content.strip() if content else None
                        voice_allowed = True
                elif ev_type == "follow":
                    if self.voice_follow.get():
                        template = self.ent_msg_follow.get().strip()
                        if template:
                            texto = template.format(user=user)
                            voice_allowed = True
                elif ev_type == "gift":
                    nombre_gift = vars_dict.get("gift", "").strip()
                    cantidad = vars_dict.get("cant", 1)
                    self.registrar_evento_gift(nombre_gift)
                    if self.voice_gift.get():
                        template = self.ent_msg_gift.get().strip()
                        if template:
                            texto = template.format(user=vars_dict.get("user", user), gift=nombre_gift, cant=cantidad)
                            voice_allowed = True

                if texto or (ev_type in ("follow", "gift")):
                    log_text = f"[{ev_type.upper()}] {user}"
                    if texto: log_text += f": {texto}"
                    self.root.after(0, self.update_log, log_text)

                if self.filters_enabled.get():
                    efectos_pendientes = []
                    for slot in self.filtros_slots:
                        ev = slot["evento"].get().strip()
                        if ev_type == "follow" and ev == "follow":
                            # Pasamos la configuración de mute del slot
                            efectos_pendientes.append((slot["filtro"].get(), slot["duracion"].get(), 1, slot["mute_var"].get()))
                        elif ev_type == "gift":
                            nombre_regalo_evento = vars_dict.get("gift", "").strip()
                            if ev == "all-gift" or ev == nombre_regalo_evento:
                                cantidad = vars_dict.get("cant", 1)
                                efectos_pendientes.append((slot["filtro"].get(), slot["duracion"].get(), cantidad, slot["mute_var"].get()))
                    
                    if efectos_pendientes:
                        for filtro, duracion, repeticiones, apply_mute in efectos_pendientes:
                            # Pasamos apply_mute a ejecutar_filtro
                            self.ejecutar_filtro(filtro, duracion, repeticiones, apply_mute=apply_mute)
                        
                        if texto and voice_allowed:
                            time.sleep(1.0)
                            self.play_audio(texto)
                    else:
                        if texto and voice_allowed:
                            self.play_audio(texto)
                else:
                    if texto and voice_allowed:
                        self.play_audio(texto)

                debe_aplicar_delay = True
                if is_priority and self.skip_delay.get(): debe_aplicar_delay = False
                if debe_aplicar_delay: time.sleep(self.delay_val.get())

                if self.queue.qsize() > 5:
                    priority = []
                    last_comment = None
                    while not self.queue.empty():
                        item = self.queue.get()
                        if item[0] in ("follow", "gift"): priority.append(item)
                        else: last_comment = item
                        self.queue.task_done()
                    for p in priority: self.queue.put(p)
                    if last_comment: self.queue.put(last_item)
                        
            except Exception as e: print("Error en voice_processor:", e)
            self.queue.task_done()
            
    def play_audio(self, text):
        if not self.is_running: return
        try:
            filename = f"tts_{int(time.time() * 1000)}.mp3"
            gTTS(text=text, lang='es').save(filename)
            pygame.mixer.music.load(filename)
            pygame.mixer.music.set_volume(self.volume_tts_val.get() / 100.0)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy(): time.sleep(0.05)
            pygame.mixer.music.unload()
            os.remove(filename)
        except Exception as e: print("Error en TTS:", e)

    def update_log(self, text):
        self.log_txt.config(state='normal')
        self.log_txt.insert(tk.END, text + "\n")
        self.log_txt.see(tk.END)
        self.log_txt.config(state='disabled')

    def log(self, text):
        """Helper para loggear desde métodos no-UI"""
        self.update_log(text)

    def toggle_bot(self):
        if self.is_testing: return
        if not self.is_running:
            errores = self.validar_filtros()
            if errores: self.mostrar_error_validacion(errores); return
            self.is_running = True
            self.btn_toggle.config(text="Detener Live")
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
            self.btn_toggle.config(text="Iniciar Live")
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
                        if key != "eventos": self.config_data[key] = value
                    self.config_data["allow_effects_mute"] = loaded.get("allow_effects_mute", True)
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
            "filters_enabled": self.filters_enabled.get(),
            "allow_effects_mute": self.allow_effects_mute.get(),
            "filtros": self.exportar_filtros(), "reconnect_interval": self.reconnect_interval.get(),
            "reconnect_attempts": self.reconnect_attempts.get(),
            "volume_tts": self.volume_tts_val.get(), "volume_effects": self.volume_effects_val.get()
        })
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            self.save_persistent_data()
        except: pass
        self.root.destroy()