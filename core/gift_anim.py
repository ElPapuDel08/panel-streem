import os
import sys
import json
import socket

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
    
# === SUPRIMIR MENSAJE DE PYGAME ===
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

def obtener_resolucion():
    """Obtiene la resolución de la pantalla principal en Windows."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except:
        return 1920, 1080 # Fallback estándar

def descubrir_efectos():
    """Descubre efectos principales y sub-efectos delegando en los módulos."""
    efectos = {}
    carpeta_effect = os.path.join(RAIZ, "effect")
    if os.path.exists(carpeta_effect):
        for archivo in os.listdir(carpeta_effect):
            if archivo.startswith("effect_") and archivo.endswith(".py"):
                nombre_modulo = archivo[:-3]
                try:
                    modulo = __import__(f"effect.{nombre_modulo}", fromlist=[''])
                    if hasattr(modulo, 'NOMBRE') and hasattr(modulo, 'ejecutar'):
                        efectos[modulo.NOMBRE] = {"tipo": "principal", "modulo": modulo}
                    if hasattr(modulo, 'listar_sub_efectos') and hasattr(modulo, 'ejecutar_especifico'):
                        for sub_nombre in modulo.listar_sub_efectos():
                            efectos[sub_nombre] = {"tipo": "especifico", "modulo": modulo}
                except Exception as e:
                    print(f"❌ Error al cargar módulo '{archivo}': {e}", file=sys.stderr)
    return efectos


# === MODO: listar efectos ===
if len(sys.argv) == 2 and sys.argv[1] == "--list-effects":
    efectos = descubrir_efectos()
    principales = sorted([n for n, c in efectos.items() if c["tipo"] == "principal"])
    especificos = sorted([n for n, c in efectos.items() if c["tipo"] == "especifico"])
    for nombre in principales: print(nombre)
    import re
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]
    especificos.sort(key=natural_sort_key)
    for nombre in especificos: print(nombre)
    sys.exit(0)

def main():
    if len(sys.argv) < 2:
        print("Uso: python gift_anim.py <efecto> <sub_tipo> [duracion_seg] [volumen%] [cantidad]", file=sys.stderr)
        sys.exit(1)

    nombre_efecto = sys.argv[1]
    sub_tipo = sys.argv[2] if len(sys.argv) > 2 else 'NULL'
    duracion_seg = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    volumen = int(sys.argv[4]) if len(sys.argv) > 4 else 100
    cantidad = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    duracion_ms = duracion_seg * 1000

    payload_list = [nombre_efecto, sub_tipo, duracion_seg, volumen, cantidad]
    
    # === MODO STANDALONE ===
    # El panel ahora maneja los efectos internamente sin necesidad de Sockets/UDP.
    # Este script sirve para ejecución manual o como respaldo.
    efectos_descubiertos = descubrir_efectos()
    if nombre_efecto not in efectos_descubiertos:
        print(f"⚠️ Efecto '{nombre_efecto}' no encontrado.", file=sys.stderr)
        sys.exit(1)

    config_efecto = efectos_descubiertos[nombre_efecto]
    modulo = config_efecto["modulo"]
    if config_efecto["tipo"] == "especifico":
        sub_tipo = nombre_efecto

    try:
        # Modo Standalone (sin Stage persistente)
        modulo.ejecutar(duracion_ms, volumen, sub_tipo, cantidad)
    except Exception as e:
        print(f"❌ Error inesperado en '{nombre_efecto}': {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
