# 🚀 TikTok Live Bot - Pro

Panel interactivo profesional diseñado para creadores de contenido en TikTok Live. Este bot permite automatizar interacciones, reproducir efectos visuales/auditivos en tiempo real y gestionar la comunidad mediante triggers inteligentes.

## ✨ Capacidades Principales
- **Interacción en Tiempo Real:** Reacciona instantáneamente a comentarios, regalos, compartidos y nuevos seguidores.
- **Sistema de Efectos Multimedia:** Ejecuta animaciones en pantalla, videos y sonidos personalizados.
- **Lienzo Global (Stage):** Los efectos se dibujan en una capa persistente transparente sobre todas tus ventanas.
- **Lectura de Voz (TTS) Avanzada:** Motor de voz con dos modos (Leer todo o solo mediante comando reservado `!s`).
- **Metadatos para Desarrolladores:** Los efectos reciben información en tiempo real (quién donó, qué mensaje envió) para crear animaciones personalizadas.
- **Optimización Anti-Lag:** Sistema de "Slots" y semáforos para evitar la sobrecarga de efectos simultáneos.

---

## 🖥️ Guía de Pestañas

### 1. 🎮 Control
Es el centro de operaciones.
- **Usuario de TikTok:** Configura el nombre de usuario de la cuenta a monitorear.
- **Iniciar Live:** Conecta/desconecta el bot con los servidores de TikTok.
- **Pre-visualizador (🧪 Test):** Abre un panel de simulación para probar todos los efectos con datos de prueba realistas.
- **Registro de Eventos:** Consola en tiempo real que muestra cada interacción detectada.

### 2. ⚙️ Ajustes
Configuración detallada del comportamiento del bot.
- **Mensajes:** Personaliza los textos de agradecimiento para follows y regalos (estas plantillas también las usan los efectos visuales).
- **Voz (TTS):** 
    - **Leer todo:** El bot lee cada comentario después del delay.
    - **Solo "!s":** El bot solo lee comentarios que empiecen con el comando reservado `!s`.
- **Sistema:** Configuración de reconexión, volumen y optimización de concurrencia.

### 3. 🎭 Efectos
Gestión de disparadores (Triggers).
- **Asignación:** Vincula eventos específicos con efectos de la carpeta `effect/`, sonidos en `song/` o videos en `video/`.
- **Argumentos Extendidos:** El script `gift_anim.py` ahora soporta un 6to argumento con el formato `Usuario|Mensaje` para efectos inteligentes.

### 4. 💬 Comandos
Gestión de comandos de chat.
- Añade comandos personalizados para activar respuestas o efectos. 
- *Nota: El comando `!s` está reservado por el sistema para la lectura selectiva.*

### 5. 🛠️ Workshop & Info
- **Workshop:** Herramientas avanzadas para la gestión de plugins y lógica extendida.
- **Info:** Guía rápida sobre el uso de muteo y recarga de efectos en caliente.

---

## 🛠️ Instalación y Uso

### Ejecución Directa
Si eres desarrollador o quieres probar cambios:
1. Asegúrate de tener el entorno virtual activo (`venv`).
2. Ejecuta `python core/main.py`.

### Uso del Ejecutable (EXE)
1. Ejecuta `TikTokPanel.exe`.
2. Asegúrate de que las carpetas `venv`, `core`, `song`, `video` y `effect` estén en la misma ubicación.

### Compilación (Opcional)
Si has realizado cambios en el código:
1. Ejecuta `build.bat`. El EXE se actualizará automáticamente en la raíz.

---
*Desarrollado para la creación de contenido interactivo y dinámico.*
