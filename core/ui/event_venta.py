# core/ui/event_venta.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys
import json
import random
from gtts import gTTS
from queue import Queue
import pygame
import emoji

# Asegurar que las importaciones directas funcionan (main.py ya agrega la base_path)
from content_tiktok import TikTokScraper

class VentaEvent:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Sistema de Ventas en Vivo")
        self.root.geometry("700x650")
        self.root.configure(bg="#f0f0f0")

        # --- Base de Datos Temporal ---
        self.cola_espera = []      # Lista de unique_ids
        self.atendidos = []        # Lista de unique_ids
        self.historial_mensajes = {} # {unique_id: [mensajes]}
        self.usuario_actual = None # Usuario en ventana de atención
        
        # --- Configuración y Persistencia ---
        self.config_dir = os.path.join("core", "profile")
        self.config_file = os.path.join(self.config_dir, "event_venta.json")
        
        self.comando_activacion = tk.StringVar(value="!venta")
        self.tts_enabled = tk.BooleanVar(value=True)
        self.leer_emojis = tk.BooleanVar(value=True)
        self.usuario_tiktok = tk.StringVar(value="tu_usuario")
        self.buscar_usuario = tk.StringVar(value="")
        
        self.load_config()
        
        self.is_running = False
        self.queue = Queue()
        self.scraper = None

        pygame.mixer.init()
        self.setup_styles()
        self.setup_ui()
        
        # Guardar automáticamente al cambiar ajustes
        self.comando_activacion.trace_add("write", lambda *a: self.save_config())
        self.tts_enabled.trace_add("write", lambda *a: self.save_config())
        self.leer_emojis.trace_add("write", lambda *a: self.save_config())
        self.usuario_tiktok.trace_add("write", lambda *a: self.save_config())
        self.buscar_usuario.trace_add("write", lambda *a: self.actualizar_vista_cola())
        
        # Iniciar procesador de colas
        self.root.after(100, self.process_queue)
        
        # Iniciar thread de voz
        self.voice_queue = Queue()
        threading.Thread(target=self.voice_processor, daemon=True).start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.save_config()
        if self.scraper:
            self.scraper.stop()
        self.root.destroy()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.comando_activacion.set(data.get("comando", "!venta"))
                    self.tts_enabled.set(data.get("tts", True))
                    self.leer_emojis.set(data.get("leer_emojis", True))
                    self.usuario_tiktok.set(data.get("usuario", "tu_usuario"))
            except Exception as e:
                print(f"Error cargando config de venta: {e}")

    def save_config(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        data = {
            "comando": self.comando_activacion.get(),
            "tts": self.tts_enabled.get(),
            "leer_emojis": self.leer_emojis.get(),
            "usuario": self.usuario_tiktok.get()
        }
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error guardando config de venta: {e}")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        bg_color = "#f0f0f0"
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 9, "bold"))
        style.configure("TNotebook", background=bg_color)
        style.configure("TNotebook.Tab", padding=[15, 5])

    def setup_ui(self):
        top_frame = tk.Frame(self.root, bg="#2c3e50", padx=10, pady=10)
        top_frame.pack(fill="x")
        
        tk.Label(top_frame, text="TikTok User:", bg="#2c3e50", fg="white", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.ent_user = tk.Entry(top_frame, textvariable=self.usuario_tiktok, font=("Segoe UI", 10), width=15)
        self.ent_user.pack(side="left", padx=5)
        
        self.btn_toggle = tk.Button(top_frame, text="▶ CONECTAR", command=self.toggle_connection, 
                                    bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), padx=10)
        self.btn_toggle.pack(side="left", padx=5)
        
        self.btn_test = tk.Button(top_frame, text="🧪 MODO TEST", command=self.open_test_mode,
                                  bg="#8e44ad", fg="white", font=("Segoe UI", 9, "bold"), padx=10)
        self.btn_test.pack(side="right", padx=5)

        # Consola de Log de Conexión
        self.log_txt = tk.Text(self.root, height=4, font=("Consolas", 9), state="disabled", bg="#f9f9f9", bd=1, relief="sunken")
        self.log_txt.pack(fill="x", padx=10, pady=(0, 5))

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_cola = ttk.Frame(self.notebook)
        self.tab_atendidos = ttk.Frame(self.notebook)
        self.tab_config = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_cola, text=" ⏳ Cola de Espera ")
        self.notebook.add(self.tab_atendidos, text=" ✅ Atendidos ")
        self.notebook.add(self.tab_config, text=" ⚙️ Configuración ")

        self.setup_cola_tab()
        self.setup_atendidos_tab()
        self.setup_config_tab()

    def setup_cola_tab(self):
        search_frame = tk.Frame(self.tab_cola, bg="#ecf0f1", pady=5, padx=10)
        search_frame.pack(fill="x")
        
        tk.Label(search_frame, text="🔍 Buscar:", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Entry(search_frame, textvariable=self.buscar_usuario, font=("Segoe UI", 9), width=25).pack(side="left", padx=5)

        btn_frame = tk.Frame(self.tab_cola, pady=5)
        btn_frame.pack(fill="x")
        
        tk.Button(btn_frame, text="🎲 ELEGIR ALEATORIO", command=self.elegir_aleatorio, 
                  bg="#f39c12", fg="white", font=("Segoe UI", 9, "bold")).pack(side="right", padx=10)
        
        tk.Label(self.tab_cola, text="Clientes esperando ser atendidos:", font=("Segoe UI", 10, "italic")).pack(anchor="w", padx=10)

        container = tk.Frame(self.tab_cola)
        container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.canvas_cola = tk.Canvas(container, highlightthickness=0)
        self.scroll_cola = ttk.Scrollbar(container, orient="vertical", command=self.canvas_cola.yview)
        self.frame_items_cola = tk.Frame(self.canvas_cola)
        
        self.frame_items_cola.bind("<Configure>", lambda e: self.canvas_cola.configure(scrollregion=self.canvas_cola.bbox("all")))
        self.canvas_cola.create_window((0,0), window=self.frame_items_cola, anchor="nw")
        self.canvas_cola.configure(yscrollcommand=self.scroll_cola.set)
        
        self.canvas_cola.pack(side="left", fill="both", expand=True)
        self.scroll_cola.pack(side="right", fill="y")

    def setup_atendidos_tab(self):
        container = tk.Frame(self.tab_atendidos)
        container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.canvas_atendidos = tk.Canvas(container, highlightthickness=0)
        self.scroll_atendidos = ttk.Scrollbar(container, orient="vertical", command=self.canvas_atendidos.yview)
        self.frame_items_atendidos = tk.Frame(self.canvas_atendidos)
        
        self.frame_items_atendidos.bind("<Configure>", lambda e: self.canvas_atendidos.configure(scrollregion=self.canvas_atendidos.bbox("all")))
        self.canvas_atendidos.create_window((0,0), window=self.frame_items_atendidos, anchor="nw")
        self.canvas_atendidos.configure(yscrollcommand=self.scroll_atendidos.set)
        
        self.canvas_atendidos.pack(side="left", fill="both", expand=True)
        self.scroll_atendidos.pack(side="right", fill="y")

    def setup_config_tab(self):
        card = tk.LabelFrame(self.tab_config, text=" Ajustes del Evento ", padx=20, pady=20)
        card.pack(fill="x", padx=20, pady=20)
        
        tk.Label(card, text="Comando de Activación:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(card, textvariable=self.comando_activacion, font=("Segoe UI", 10)).grid(row=0, column=1, sticky="ew", padx=10)
        
        tk.Checkbutton(card, text="Activar Voz (TTS) para usuario atendido", variable=self.tts_enabled).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        tk.Checkbutton(card, text="Traducir Emojis a Voz", variable=self.leer_emojis).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        
        tk.Label(card, text="Instrucciones:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w")
        tk.Label(card, text="1. Los usuarios deben escribir el comando para entrar en la lista.\n2. Solo se registran mensajes de usuarios en espera o atención.\n3. Una vez finalizados, no pueden re-entrar hasta ser eliminados de 'Atendidos'.", 
                 justify="left", font=("Segoe UI", 9)).grid(row=3, column=0, columnspan=2, sticky="w")

    def on_event_received(self, event_type, user, message, data):
        self.queue.put((event_type, user, message, data))
        
        # Log para depuración visual en la interfaz
        if event_type == "comment":
            self.log(f"🗨️ {user}: {message}")
        elif event_type == "follow":
            self.log(f"➕ {user} empezó a seguirte")
        elif event_type == "gift":
            gift_name = data.get("gift", "regalo")
            cant = data.get("cant", 1)
            self.log(f"🎁 {user} envió {cant} {gift_name}")

    def process_queue(self):
        while not self.queue.empty():
            etype, user, msg, data = self.queue.get()
            if etype == "comment":
                cmd = self.comando_activacion.get().strip().lower()
                clean_msg = msg.strip().lower()
                if clean_msg == cmd:
                    if user not in self.cola_espera and user not in self.atendidos and user != self.usuario_actual:
                        self.cola_espera.append(user)
                        self.historial_mensajes[user] = []
                        self.actualizar_vista_cola()
                        self.speak(f"Nuevo cliente en espera: {user}")
                if user in self.historial_mensajes or user == self.usuario_actual:
                    if user not in self.historial_mensajes: self.historial_mensajes[user] = []
                    self.historial_mensajes[user].append(msg)
                    if user == self.usuario_actual and hasattr(self, 'atencion_win') and self.atencion_win.winfo_exists():
                        self.append_msg_to_view(user, msg)
                        if self.tts_enabled.get():
                            self.speak(msg)
        self.root.after(100, self.process_queue)

    def log(self, text):
        self.log_txt.config(state="normal")
        self.log_txt.insert("end", f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.log_txt.see("end")
        self.log_txt.config(state="disabled")

    def mostrar_error_conexion(self, mensaje):
        self.is_running = False
        self.btn_toggle.config(text="▶ CONECTAR", bg="#27ae60")
        self.log(f"❌ ERROR: {mensaje}")
        messagebox.showerror("TikTok Live", mensaje)

    def actualizar_vista_cola(self):
        for w in self.frame_items_cola.winfo_children(): w.destroy()
        search_term = self.buscar_usuario.get().strip().lower()
        for i, user in enumerate(self.cola_espera):
            if search_term and search_term not in user.lower():
                continue
            item = tk.Frame(self.frame_items_cola, bg="white", bd=1, relief="groove", pady=5, padx=10)
            item.pack(fill="x", pady=2)
            tk.Label(item, text=f"👤 {user}", bg="white", font=("Segoe UI", 10, "bold")).pack(side="left")
            tk.Button(item, text="VENTA", command=lambda u=user: self.abrir_atencion(u),
                      bg="#2ecc71", fg="white", font=("Segoe UI", 8, "bold"), bd=0, padx=10).pack(side="right")
            msg_count = len(self.historial_mensajes.get(user, []))
            tk.Label(item, text=f"{msg_count} msgs", bg="white", fg="#7f8c8d", font=("Segoe UI", 8)).pack(side="right", padx=10)

    def actualizar_vista_atendidos(self):
        for w in self.frame_items_atendidos.winfo_children(): w.destroy()
        for user in self.atendidos:
            item = tk.Frame(self.frame_items_atendidos, bg="#f9f9f9", bd=1, relief="flat", pady=5, padx=10)
            item.pack(fill="x", pady=2)
            tk.Label(item, text=f"✔️ {user}", bg="#f9f9f9", fg="#27ae60", font=("Segoe UI", 10)).pack(side="left")
            tk.Button(item, text="X", command=lambda u=user: self.remover_atendido(u),
                      bg="#e74c3c", fg="white", font=("Segoe UI", 8, "bold"), bd=0, padx=5).pack(side="right")

    def elegir_aleatorio(self):
        if not self.cola_espera:
            messagebox.showinfo("Cola vacía", "No hay usuarios en espera.")
            return
        user = random.choice(self.cola_espera)
        self.abrir_atencion(user)

    def abrir_atencion(self, user):
        if user in self.cola_espera:
            self.usuario_actual_index = self.cola_espera.index(user)
            self.cola_espera.remove(user)
            self.actualizar_vista_cola()
        else:
            self.usuario_actual_index = None
        self.usuario_actual = user
        self.atencion_win = tk.Toplevel(self.root)
        self.atencion_win.title(f"Atendiendo a: {user}")
        self.atencion_win.geometry("500x650")
        self.atencion_win.protocol("WM_DELETE_WINDOW", self.dejar_en_espera)
        header = tk.Frame(self.atencion_win, bg="#3498db", pady=15)
        header.pack(fill="x")
        tk.Label(header, text=f"CLIENTE: {user}", bg="#3498db", fg="white", font=("Segoe UI", 14, "bold")).pack()
        msg_frame = tk.Frame(self.atencion_win, padx=10, pady=10)
        msg_frame.pack(fill="both", expand=True)
        self.txt_atencion = tk.Text(msg_frame, font=("Segoe UI", 11), state="disabled", bg="#fdfefe", bd=1, relief="solid")
        self.txt_atencion.pack(fill="both", expand=True)
        for m in self.historial_mensajes.get(user, []):
            self.append_msg_to_view(user, m)
        footer = tk.Frame(self.atencion_win, pady=20, bg="#f0f0f0")
        footer.pack(fill="x", side="bottom")
        
        tk.Button(footer, text="⏸ DEJAR EN ESPERA", command=self.dejar_en_espera,
                  bg="#95a5a6", fg="white", font=("Segoe UI", 10, "bold"), padx=25, pady=10).pack(side="left", padx=20)
                  
        tk.Button(footer, text="🏁 FINALIZAR VENTA", command=self.finalizar_venta,
                  bg="#2ecc71", fg="white", font=("Segoe UI", 10, "bold"), padx=25, pady=10).pack(side="right", padx=20)

    def append_msg_to_view(self, user, msg):
        self.txt_atencion.config(state="normal")
        self.txt_atencion.insert("end", f"[{time.strftime('%H:%M')}] ", "time")
        self.txt_atencion.insert("end", f"{user}: ", "user")
        self.txt_atencion.insert("end", f"{msg}\n", "msg")
        self.txt_atencion.tag_config("time", foreground="#95a5a6")
        self.txt_atencion.tag_config("user", foreground="#2980b9", font=("Segoe UI", 11, "bold"))
        self.txt_atencion.see("end")
        self.txt_atencion.config(state="disabled")

    def dejar_en_espera(self):
        user = self.usuario_actual
        if user:
            index = getattr(self, "usuario_actual_index", None)
            if index is not None and index <= len(self.cola_espera):
                self.cola_espera.insert(index, user)
            else:
                self.cola_espera.append(user)
            self.usuario_actual = None
            self.actualizar_vista_cola()
        self.atencion_win.destroy()

    def finalizar_venta(self):
        user = self.usuario_actual
        if user:
            self.atendidos.append(user)
            if user in self.historial_mensajes: del self.historial_mensajes[user]
            self.usuario_actual = None
            self.actualizar_vista_atendidos()
        self.atencion_win.destroy()

    def remover_atendido(self, user):
        if user in self.atendidos:
            self.atendidos.remove(user)
            self.actualizar_vista_atendidos()

    def toggle_connection(self):
        if not self.is_running:
            user = self.usuario_tiktok.get().strip()
            if not user:
                messagebox.showerror("Error", "Ingresa un usuario de TikTok")
                return
            self.is_running = True
            self.btn_toggle.config(text="🛑 DETENER", bg="#e74c3c")
            self.log(f"Intentando conectar con @{user}...")
            self.scraper = TikTokScraper(user, self.on_event_received, error_callback=self.mostrar_error_conexion)
            # Sincronizar reintentos si fuera necesario
            self.scraper.max_reintentos = 5
            self.scraper.intervalo_reintento = 10
            threading.Thread(target=self.scraper.run, daemon=True).start()
        else:
            self.is_running = False
            self.btn_toggle.config(text="▶ CONECTAR", bg="#27ae60")
            if self.scraper: 
                self.scraper.stop()
            self.log("Desconectado.")

    def open_test_mode(self):
        tw = tk.Toplevel(self.root)
        tw.title("Simulador de Eventos (Venta)")
        tw.geometry("300x200")
        tk.Label(tw, text="Simular Comentario:").pack(pady=5)
        ent = tk.Entry(tw)
        ent.pack(padx=10)
        ent.insert(0, "!venta")
        tk.Label(tw, text="Usuario:").pack(pady=5)
        u_ent = tk.Entry(tw)
        u_ent.pack(padx=10)
        u_ent.insert(0, f"User_{random.randint(100,999)}")
        def simular():
            self.on_event_received("comment", u_ent.get(), ent.get(), {})
        tk.Button(tw, text="ENVIAR", command=simular, bg="#3498db", fg="white").pack(pady=10)

    def speak(self, text):
        if not self.tts_enabled.get(): return
        self.voice_queue.put(text)

    def voice_processor(self):
        while True:
            text = self.voice_queue.get()
            try:
                # Procesar emojis si está habilitado
                if self.leer_emojis.get():
                    # Convertir emojis a texto (ej: :smile: -> "cara sonriente")
                    # Usamos language='es' para descripciones en español
                    text = emoji.demojize(text, language='es').replace(":", " ").replace("_", " ")
                
                clean_text = ''.join(c for c in text if c.isprintable())
                if not clean_text: continue
                tts = gTTS(text=clean_text, lang='es')
                filename = f"tmp_venta_tts_{int(time.time())}.mp3"
                tts.save(filename)
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy(): time.sleep(0.1)
                pygame.mixer.music.unload()
                if os.path.exists(filename): os.remove(filename)
            except Exception as e: print(f"Error TTS: {e}")
            finally: self.voice_queue.task_done()

def start():
    root = tk.Tk()
    app = VentaEvent(root)
    root.mainloop()

if __name__ == "__main__":
    start()