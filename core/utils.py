"""
core/utils.py
Funciones de utilidad para manejo de rutas.
- resource_path: para archivos internos empaquetados en el EXE (solo lectura).
- external_path: para archivos externos que deben existir junto al EXE (editable por el usuario).
- get_python_executable: resuelve el intérprete Python real (evita el bucle infinito en EXE).
"""
import sys
import os


def resource_path(relative_path: str) -> str:
    """
    Retorna la ruta absoluta al recurso.
    - En desarrollo: usa la carpeta raíz del proyecto.
    - Empaquetado con PyInstaller (--onefile): usa sys._MEIPASS (carpeta temporal de extracción).
    Útil para archivos de solo lectura incluidos en el EXE.
    """
    try:
        # Cuando se ejecuta como EXE (onefile), los archivos se extraen aquí
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        # En desarrollo, la raíz del proyecto
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def external_path(relative_path: str) -> str:
    """
    Retorna la ruta absoluta a un archivo EXTERNO al EXE.
    Siempre apunta a la carpeta donde está el EXE (o la raíz del proyecto en desarrollo).
    Útil para archivos que el usuario puede editar (config.json, data.json, etc.).
    """
    if getattr(sys, 'frozen', False):
        # Ejecutándose como EXE compilado
        base_path = os.path.dirname(sys.executable)
    else:
        # En desarrollo, raíz del proyecto
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def get_python_executable() -> str:
    """
    Retorna la ruta al intérprete Python real para usar en subprocesos.

    PROBLEMA: Al empaquetar con PyInstaller, sys.executable apunta al EXE
    compilado, NO a python.exe. Llamar subprocess con sys.executable causaría
    que el EXE se ejecute a sí mismo infinitamente.

    SOLUCIÓN: Si estamos en un EXE frozen, busca python.exe en el venv que
    está junto al EXE. En desarrollo, retorna sys.executable normalmente.
    """
    if not getattr(sys, 'frozen', False):
        # En desarrollo: sys.executable ES python.exe, todo bien.
        return sys.executable

    # Estamos dentro de un EXE compilado.
    # Buscamos python.exe en el venv relativo a la carpeta del EXE.
    exe_dir = os.path.dirname(sys.executable)

    # Rutas candidatas del venv (en orden de preferencia)
    candidates = [
        os.path.join(exe_dir, "venv", "Scripts", "python.exe"),
        os.path.join(exe_dir, "python.exe"),
        os.path.join(exe_dir, "..", "venv", "Scripts", "python.exe"),
    ]

    for candidate in candidates:
        normalized = os.path.normpath(candidate)
        if os.path.isfile(normalized):
            return normalized

    # Fallback: retornar sys.executable aunque apunte al EXE.
    # Esto puede causar problemas, pero es mejor que fallar silenciosamente.
    return sys.executable
