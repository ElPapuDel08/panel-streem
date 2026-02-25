# effect/effect_sonidoR.py
import os
import sys
import pygame
import random
import time

# === METADATOS ===
NOMBRE = "sonidoR"
VERSION = "1.0"

# Inicializar pygame una vez
pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
pygame.mixer.init()

# Caché para evitar recargar archivos en combos
SOUND_CACHE = {}

# === FUNCIÓN PRINCIPAL ===
def ejecutar(duracion_ms=None, volumen=100, sub_tipo='NULL', cantidad=1, parent=None):
    """
    Ejecuta el efecto de sonido.
    Si sub_tipo es 'NULL', elige uno aleatorio.
    Si sub_tipo es un nombre (con o sin 'song_'), reproduce ese.
    Repite el proceso 'cantidad' veces.
    """
    for i in range(cantidad):
        if sub_tipo == 'NULL':
            # Lógica aleatoria original
            ruta_sonidos = "song"
            if not os.path.exists(ruta_sonidos):
                return {"error": "Carpeta 'song/' no encontrada."}
            archivos = [f for f in os.listdir(ruta_sonidos) if f.endswith('.mp3') and f.split('_', 1)[0].isdigit()]
            if not archivos:
                return {"error": "No hay sonidos válidos en 'song/'."}
            sonido_elegido = random.choice(archivos)
            nombre_a_ejecutar = os.path.splitext(sonido_elegido)[0]
        else:
            nombre_a_ejecutar = sub_tipo

        res = ejecutar_especifico(nombre_a_ejecutar, duracion_ms, volumen)
        if "error" in res:
            return res
        
        if cantidad > 1 and i < cantidad - 1:
            time.sleep(0.1) # Pequeña pausa entre repeticiones
            
    return {"mensaje": f"Efecto '{NOMBRE}' ejecutado {cantidad} veces."}
    
# === FUNCIÓN PARA LISTAR SONIDOS DISPONIBLES ===
def listar_sub_efectos():
    """Descubre sonidos en song/ y los devuelve con el prefijo 'song_'."""
    ruta_sonidos = "song"
    if not os.path.exists(ruta_sonidos):
        return []

    sub_efectos = []
    for f in os.listdir(ruta_sonidos):
        if f.endswith('.mp3'):
            partes = f.split('_', 1)
            if partes and partes[0].isdigit():
                nombre = os.path.splitext(f)[0]
                sub_efectos.append(f"song_{nombre}")
    
    return sorted(sub_efectos)

# === FUNCIÓN PARA REPRODUCIR SONIDO ESPECÍFICO ===
def ejecutar_especifico(nombre_especifico, duracion_ms=None, volumen=100):
    """Reproduce un archivo MP3 específico desde song/."""
    # Quitar prefijo 'song_' si está presente para buscar el archivo real
    nombre_archivo = nombre_especifico
    if nombre_especifico.startswith("song_"):
        nombre_archivo = nombre_especifico[5:] # quitar 'song_'

    ruta_sonidos = "song"
    ruta_completa = os.path.join(ruta_sonidos, f"{nombre_archivo}.mp3")
    
    if not os.path.exists(ruta_completa):
        return {"error": f"Archivo '{nombre_archivo}.mp3' no encontrado en 'song/'."}

    try:
        if ruta_completa not in SOUND_CACHE:
            SOUND_CACHE[ruta_completa] = pygame.mixer.Sound(ruta_completa)
        
        sound = SOUND_CACHE[ruta_completa]
        sound.set_volume(max(0.0, min(1.0, volumen / 100.0)))
        
        dur_real_ms = int(sound.get_length() * 1000)
        final_dur = duracion_ms if (duracion_ms and duracion_ms > 0) else dur_real_ms
        
        channel = sound.play()
        # Bloqueamos para que el semáforo del panel cuente este slot como ocupado
        time.sleep(final_dur / 1000.0)
        
        if channel:
            try: channel.stop()
            except: pass
            
        return {"mensaje": f"Sonido '{nombre_archivo}' reproducido y finalizado tras {final_dur}ms."}
    except Exception as e:
        return {"error": f"Error al reproducir '{nombre_archivo}.mp3': {str(e)}"}