#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import subprocess
import os

def ajustar_volumen_maximo(nivel="100%"):
    time.sleep(3)

    # Lista extendida de comandos a intentar.
    comandos_a_intentar = [
        # 1. Método moderno con PulseAudio (si está disponible).
        ['pactl', 'set-sink-volume', '@DEFAULT_SINK@', nivel],

        # 2. Forzar nivel en la tarjeta de sonido principal (card 0).
        ['amixer', '-c', '0', 'sset', 'Master', nivel],
        ['amixer', '-c', '0', 'sset', 'PCM', nivel],

        # 3. Fallbacks generales (si los anteriores fallan).
        ['amixer', 'sset', 'Master', nivel],
        ['amixer', 'sset', 'PCM', nivel],
        ['amixer', 'sset', 'Master Playback Volume', nivel]
    ]

    for comando in comandos_a_intentar:
        try:
            print(f"Intentando con: {' '.join(comando)}")
            subprocess.run(
                comando,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"Éxito: El volumen se ajustó con el comando: '{' '.join(comando)}'.")

        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Falló el comando: '{comando[0]}'. Probando el siguiente...")

    return
# --- INICIO DE TU PROGRAMA PRINCIPAL ---

# ... Aquí sigue el resto de tu código ...
print("Iniciando la lógica principal de la Tabla Periódica Auditiva...")

# --- VARIABLES DE ESTADO GLOBAL ---
proceso_reproductor_actual = None
fila_seleccionada = None
columna_seleccionada = None
tiempo_de_primera_seleccion = None
tipo_primera_seleccion = None
bloqueo_callback = False
# Variables añadidas para la lógica de la explicación
pin_primera_seleccion = None
puede_sonar_explicacion = True
es_pulsacion_repetida = False

# --- CONFIGURACIÓN ---
TIMEOUT_SEGUNDOS = 5
# NUEVAS CONSTANTES PARA LAS CARPETAS
CARPETA_AUDIOS_DIVULGACAO = "_audios_divulgacao" # Si se pulsa FILA primero
CARPETA_AUDIOS_TECNICOS = "_audios_tecnicos"     # Si se pulsa COLUMNA primero
AUDIO_ERROR = "missing_element.mp3"
AUDIO_EXPLICACION = "presentacion.mp3" # Audio de explicación

# --- MAPA LÓGICO DE LA TABLA PERIÓDICA (SIN CAMBIOS) ---

ELEMENT_MAP = {
    # ... (el diccionario ELEMENT_MAP no cambia, se mantiene igual que antes) ...
    # --- Fila 1 (Activada con Botón 1) ---
    (1, 10): 1, (1, 28): 2,
    # --- Fila 2 (Activada con Botón 2) ---
    (2, 10): 3, (2, 11): 4, (2, 23): 5, (2, 24): 6, (2, 25): 7, (2, 26): 8, (2, 27): 9, (2, 28): 10,
    # --- Fila 3 (Activada con Botón 3) ---
    (3, 10): 11, (3, 11): 12, (3, 23): 13, (3, 24): 14, (3, 25): 15, (3, 26): 16, (3, 27): 17, (3, 28): 18,
    # --- Fila 4 (Activada con Botón 4) ---
    (4, 10): 19, (4, 11): 20, (4, 12): 21, (4, 14): 22, (4, 15): 23, (4, 16): 24, (4, 17): 25, (4, 18): 26, (4, 19): 27, (4, 20): 28, (4, 21): 29, (4, 22): 30, (4, 23): 31, (4, 24): 32, (4, 25): 33, (4, 26): 34, (4, 27): 35, (4, 28): 36,
    # --- Fila 5 (Activada con Botón 5) ---
    (5, 10): 37, (5, 11): 38, (5, 12): 39, (5, 14): 40, (5, 15): 41, (5, 16): 42, (5, 17): 43, (5, 18): 44, (5, 19): 45, (5, 20): 46, (5, 21): 47, (5, 22): 48, (5, 23): 49, (5, 24): 50, (5, 25): 51, (5, 26): 52, (5, 27): 53, (5, 28): 54,
    # --- Fila 6 (Activada con Botón 6) ---
    (6, 10): 55, (6, 11): 56, (6, 12): 57, (6, 14): 72, (6, 15): 73, (6, 16): 74, (6, 17): 75, (6, 18): 76, (6, 19): 77, (6, 20): 78, (6, 21): 79, (6, 22): 80, (6, 23): 81, (6, 24): 82, (6, 25): 83, (6, 26): 84, (6, 27): 85, (6, 28): 86,
    # --- Fila 7 (Activada con Botón 7) ---
    (7, 10): 87, (7, 11): 88, (7, 12): 89, (7, 14): 104, (7, 15): 105, (7, 16): 106, (7, 17): 107, (7, 18): 108, (7, 19): 109, (7, 20): 110, (7, 21): 111, (7, 22): 112, (7, 23): 113, (7, 24): 114, (7, 25): 115, (7, 26): 116, (7, 27): 117, (7, 28): 118,
    # --- Fila 8 (Lantánidos, activada con Botón 8) ---
    (9, 13): 58,  (9, 14): 59,  (9, 15): 60,  (9, 16): 61,  (9, 17): 62, (9, 18): 63,  (9, 19): 64,  (9, 20): 65,  (9, 21): 66,  (9, 22): 67,  (9, 23): 68, (9, 24): 69,  (9, 25): 70,  (9, 26): 71,
    # --- Fila 9 (Actínidos, activada con Botón 9) ---
    (8, 13): 90,  (8, 14): 91,  (8, 15): 92,  (8, 16): 93,  (8, 17): 94, (8, 18): 95,  (8, 19): 96,  (8, 20): 97,  (8, 21): 98,  (8, 22): 99,  (8, 23): 100, (8, 24): 101, (8, 25): 102, (8, 26): 103,
}

# --- MAPEO DE PINES GPIO (SIN CAMBIOS) ---
MAPEO_PULSADORES = {
    # ... (el diccionario MAPEO_PULSADORES no cambia, se mantiene igual que antes) ...
    0: ('fila', 1), 1: ('fila', 2), 4: ('fila', 3), 27: ('fila', 4), 21: ('fila', 5), 13: ('fila', 6), 26: ('fila', 7), 2: ('fila', 8), 3: ('fila', 9),
    24: ('columna', 10), 25: ('columna', 11), 5: ('columna', 12), 6: ('columna', 13), 16: ('columna', 14), 14: ('columna', 15), 15: ('columna', 16), 23: ('columna', 17), 22: ('columna', 18), 12: ('columna', 19), 20: ('columna', 20), 19: ('columna', 21),
    10: ('columna', 22), 9: ('columna', 23), 11: ('columna', 24), 8: ('columna', 25), 7: ('columna', 26), 17: ('columna', 27), 18: ('columna', 28)
}

PINS_A_MONITORIZAR = list(MAPEO_PULSADORES.keys())

# --- FUNCIONES AUXILIARES ---
def detener_reproductor_anterior():
    global proceso_reproductor_actual
    if proceso_reproductor_actual and proceso_reproductor_actual.poll() is None:
        proceso_reproductor_actual.kill()
        proceso_reproductor_actual.wait()

def resetear_estado():
    global fila_seleccionada, columna_seleccionada, tiempo_de_primera_seleccion, tipo_primera_seleccion, pin_primera_seleccion, es_pulsacion_repetida, puede_sonar_explicacion
    fila_seleccionada = None
    columna_seleccionada = None
    tiempo_de_primera_seleccion = None
    tipo_primera_seleccion = None
    pin_primera_seleccion = None
    es_pulsacion_repetida = False # <-- AÑADIR ESTA LÍNEA
    puede_sonar_explicacion = True # <-- AÑADIR ESTA LÍNEA
    print("----------------------------------------")
    print("▶️  Sistema reseteado. Esperando nueva selección.")

def realizar_accion(fila, columna, primer_tipo):
    # MODIFICADO: Acepta un nuevo argumento y elige la carpeta de audio
    global proceso_reproductor_actual
    detener_reproductor_anterior()
    print(f"✅ Combinación final: (Botón Fila: {fila}, Botón Columna: {columna})")

    # Lógica para elegir la carpeta correcta
    if primer_tipo == 'fila':
        carpeta_audios = CARPETA_AUDIOS_DIVULGACAO
    else: # primer_tipo es 'columna'
        carpeta_audios = CARPETA_AUDIOS_TECNICOS
    print(f"   📂 Usando audios de la carpeta: '{carpeta_audios}'")

    elemento_numero = ELEMENT_MAP.get((fila, columna))

    if elemento_numero is None:
        print(f"   ❌ Combinación inválida. Reproduciendo sonido de error.")
        # MODIFICADO: Añadido '-q' para modo silencioso
        if os.path.exists(AUDIO_ERROR):
            comando = ['mpg123', '-q', AUDIO_ERROR]
            proceso_reproductor_actual = subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            print(f"   AVISO: No se encontró el archivo de error '{AUDIO_ERROR}'")
        return

    nombre_archivo = f"{elemento_numero:003d}.mp3"
    ruta_completa = os.path.join(carpeta_audios, nombre_archivo)

    if os.path.exists(ruta_completa):
        print(f"   🔊 Reproduciendo elemento {elemento_numero}: {ruta_completa}")
        # MODIFICADO: Añadido '-q' para modo silencioso
        comando = ['mpg123', '-q', ruta_completa]
    else:
        print(f"   ⚠️  ¡Archivo no encontrado! '{ruta_completa}'")
        print(f"   Fallback: Anunciando número de elemento {elemento_numero}.")
        texto_a_decir = f"Elemento {elemento_numero}"
        comando = ['espeak', '-v', 'es-la', '-a', '200', '-s', '150', texto_a_decir]

    proceso_reproductor_actual = subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# --- FUNCIÓN DE CALLBACK PRINCIPAL ---
# --- FUNCIÓN DE CALLBACK PRINCIPAL (CORREGIDA PARA EL SONIDO) ---
def boton_presionado_callback(channel):
    global fila_seleccionada, columna_seleccionada, tiempo_de_primera_seleccion, tipo_primera_seleccion, bloqueo_callback, pin_primera_seleccion, puede_sonar_explicacion, es_pulsacion_repetida

    # Lógica para detectar interrupción (se mantiene igual)
    if tiempo_de_primera_seleccion is None and proceso_reproductor_actual and proceso_reproductor_actual.poll() is None:
        print("INFO: Explicación interrumpida. No se reproducirá de nuevo en este ciclo.")
        puede_sonar_explicacion = False

    # Anti-rebote (se mantiene igual)
    if bloqueo_callback:
        return
    bloqueo_callback = True
    time.sleep(0.05)
    if GPIO.input(channel) != GPIO.LOW:
        bloqueo_callback = False
        return

    # --- INICIO DE LA MODIFICACIÓN ---

    # 1. Obtenemos la información del botón PRIMERO.
    info_boton = MAPEO_PULSADORES.get(channel)
    if not info_boton:
        bloqueo_callback = False
        return
    tipo_boton, numero_logico = info_boton

    # 2. REPRODUCIMOS EL SONIDO DEL BOTÓN INMEDIATAMENTE.
    #    Esto le da la máxima prioridad.
    print(f"\n🔘 Pulsado: {tipo_boton.capitalize()} {numero_logico} (Pin: {channel})")
    comando_sonido = "play -n synth 0.15 pluck G3" if tipo_boton == 'fila' else "play -n synth 0.15 pluck E5"
    subprocess.Popen(comando_sonido, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 3. AHORA, detenemos cualquier audio largo que estuviera sonando.
    detener_reproductor_anterior()

    # --- FIN DE LA MODIFICACIÓN ---

    # El resto de la lógica de selección (CASO 1 y CASO 2) se mantiene intacta.
    # CASO 1: Es la primera pulsación de una secuencia.
    if tipo_primera_seleccion is None:
        print("▶️  Iniciando nueva selección.")
        if tipo_boton == 'fila':
            fila_seleccionada = numero_logico
        else:
            columna_seleccionada = numero_logico
        pin_primera_seleccion = channel
        tipo_primera_seleccion = tipo_boton
        tiempo_de_primera_seleccion = time.time()
        es_pulsacion_repetida = False

    # CASO 2: Ya había un botón seleccionado.
    else:
        # SUB-CASO 2.1: El nuevo botón es del MISMO tipo.
        if tipo_boton == tipo_primera_seleccion:
            print(f"🔄 Selección cambiada. La nueva {tipo_boton} activa es {numero_logico}.")
            es_pulsacion_repetida = (pin_primera_seleccion == channel)
            if tipo_boton == 'fila':
                fila_seleccionada = numero_logico
                columna_seleccionada = None
            else:
                columna_seleccionada = numero_logico
                fila_seleccionada = None
            pin_primera_seleccion = channel
            tiempo_de_primera_seleccion = time.time()
        # SUB-CASO 2.2: El nuevo botón es de tipo DIFERENTE.
        else:
            print("--- ¡Combinación detectada! Realizando acción. ---")
            if tipo_boton == 'fila':
                fila_seleccionada = numero_logico
            else:
                columna_seleccionada = numero_logico
            realizar_accion(fila_seleccionada, columna_seleccionada, tipo_primera_seleccion)
            resetear_estado()

    # IMPORTANTE: Hemos movido la reproducción del sonido al principio,
    # por lo que ya no es necesaria aquí al final.

    # Pequeña pausa final para estabilizar y liberar bloqueo.
    time.sleep(0.2)
    bloqueo_callback = False


# Llama a la función para ajustar el volumen al empezar
ajustar_volumen_maximo()

# --- PROGRAMA PRINCIPAL ---
try:
    GPIO.setmode(GPIO.BCM)
    print("✅ Sistema de Tabla Periódica Auditiva v4.0 (con audio dual) iniciado.")
    resetear_estado()

    # MODIFICADO: Comprueba la existencia de AMBAS carpetas
    for carpeta in [CARPETA_AUDIOS_DIVULGACAO, CARPETA_AUDIOS_TECNICOS]:
        if not os.path.isdir(carpeta):
            print(f"AVISO: Creando carpeta '{carpeta}'.")
            os.makedirs(carpeta)

    for pin in PINS_A_MONITORIZAR:
        try:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(pin, GPIO.FALLING, callback=boton_presionado_callback, bouncetime=200)
        except (ValueError, RuntimeError) as e:
            print(f"ADVERTENCIA: No se pudo configurar el pin GPIO {pin}. Es posible que no exista. Error: {e}")

    while True:
        # Comprobamos primero si hay una selección activa y ha superado el tiempo límite.
        if tiempo_de_primera_seleccion and (time.time() - tiempo_de_primera_seleccion > TIMEOUT_SEGUNDOS):

            # CASO A: El permiso para sonar está activo (comportamiento normal).
            if puede_sonar_explicacion and not es_pulsacion_repetida:
                print("\n⏰ ¡Tiempo de selección agotado! Reproduciendo explicación.")
                detener_reproductor_anterior()

                if os.path.exists(AUDIO_EXPLICACION):
                    comando = ['mpg123', '-q', AUDIO_EXPLICACION]
                    proceso_reproductor_actual = subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    print(f"   AVISO: No se encontró el archivo de explicación '{AUDIO_EXPLICACION}'")

            # CASO B: El permiso fue revocado por una interrupción.
            else:
                print("\n⏰ ¡Tiempo de selección agotado! Reseteo silencioso tras interrupción.")

            # En ambos casos de timeout, el sistema debe volver a su estado inicial.
            resetear_estado()

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n🛑 Programa terminado por el usuario.")
except Exception as e:
    print(f"\nHa ocurrido un error inesperado: {e}")
finally:
    detener_reproductor_anterior()
    print("🧹 Limpiando la configuración de los pines GPIO...")
    GPIO.cleanup()
    print("¡Listo!")