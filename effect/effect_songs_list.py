# effect/effect_songs_list.py
import os
import pygame
import time

# === METADATOS ===
NOMBRE = "Lista de Canciones" # El nombre que aparecerá en la UI (ej. "Lista de Canciones : 1_musica")
LISTA = [] # Se llenará al importar

# Inicializar mixer (Pygame se puede inicializar varias veces, pero pre_init ayuda)
pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
pygame.mixer.init()

def cargar_archivos():
    """Escanea song/ y llena la lista global."""
    global LISTA
    LISTA = []
    ruta = "song"
    if not os.path.exists(ruta): return

    # Filtramos solo archivos que sigan un patrón simple para efectos
    for f in os.listdir(ruta):
        if f.endswith('.mp3'):
            nombre = os.path.splitext(f)[0]
            LISTA.append(nombre)
    
    LISTA.sort() # Orden alfabético

# Ejecutamos la carga al importar el módulo
cargar_archivos()

def ejecutar(nombre_archivo, duracion_ms=None, volumen=100):
    """
    Ejecuta un archivo específico de la lista.
    """
    ruta_sonidos = "song"
    ruta_completa = os.path.join(ruta_sonidos, f"{nombre_archivo}.mp3")
    
    if not os.path.exists(ruta_completa):
        return {"error": f"Archivo '{nombre_archivo}.mp3' no encontrado."}

    try:
        pygame.mixer.music.load(ruta_completa)
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volumen / 100.0)))
        pygame.mixer.music.play()
        
        if duracion_ms is not None and duracion_ms > 0:
            time.sleep(duracion_ms / 1000.0)
            pygame.mixer.music.stop()
        else:
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
        
        return {"mensaje": f"Canción '{nombre_archivo}' reproducida."}
    except Exception as e:
        return {"error": f"Error al reproducir '{nombre_archivo}': {str(e)}"}