#!/usr/bin/env python3

import configparser
from rpi_hardware_pwm import HardwarePWM
import psutil
import time
import sys
import atexit
import syslog
import os
import signal

#Inicializa las variables
canal_pwm = 0
frecuencia = 25000
ciclo_de_trabajo_anterior = 0
temperatura_anterior = 0
tiempo = 6
ciclo_de_trabajo = 0

pwm = HardwarePWM(canal_pwm, frecuencia)

def print_debug(mensaje):
    if debug and not as_a_service:
        print(mensaje)
    if debug and as_a_service:
        syslog.syslog(syslog.LOG_INFO, mensaje)
        
def inicializar_configuracion():
    # Valores predeterminados
    defaults = {
        'intervalo_de_prueba': 5,
        'canal_pwm': 0,
        'frecuencia': 25000,
        'temp_min': 45,
        'temp_max': 65,
        'ciclo_min': 60,
        'ciclo_max': 100,
        'histeresis': 2,
        'debug': False,
        'as_a_service': True
    }

    try:
        # Cargar configuración desde el archivo INI
        config = configparser.ConfigParser()
        config.read("temperature_pwm_controller.ini")

        # Desempaquetar la configuración o usar valores predeterminados
        intervalo_de_prueba = config.getint("config", "intervalo_de_prueba", fallback=defaults['intervalo_de_prueba'])
        canal_pwm = config.getint("config", "canal_pwm", fallback=defaults['canal_pwm'])
        frecuencia = config.getint("config", "frecuencia", fallback=defaults['frecuencia'])
        temp_min = config.getint("config", "temp_min", fallback=defaults['temp_min'])
        temp_max = config.getint("config", "temp_max", fallback=defaults['temp_max'])
        ciclo_min = config.getint("config", "ciclo_min", fallback=defaults['ciclo_min'])
        ciclo_max = config.getint("config", "ciclo_max", fallback=defaults['ciclo_max'])
        histeresis = config.getint("config", "histeresis", fallback=defaults['histeresis'])
        debug = config.getboolean("config", "debug", fallback=defaults['debug'])
        as_a_service = config.getboolean("config", "as_a_service", fallback=defaults['as_a_service'])

        return (intervalo_de_prueba, canal_pwm, frecuencia, temp_min, temp_max, ciclo_min, ciclo_max, histeresis, debug, as_a_service)

    except Exception as e:
        print(f"Error al cargar la configuración: {str(e)}")
        syslog.syslog(syslog.LOG_ERR, f"Error al cargar la configuración: {str(e)}")
        # Utiliza los valores predeterminados si hay un error al cargar la configuración
        return tuple(defaults.values())

def calcular_ciclo_de_trabajo(temp, temp_min, temp_max, ciclo_min, ciclo_max, ciclo_actual, hysteresis):
    try:
        if temp < temp_min:
            return 0
        elif temp > temp_max:
            return 100
        elif temp_min <= temp <= temp_max:
            if temp > temperatura_anterior + hysteresis or temp < temperatura_anterior - hysteresis:
                ciclo = (temp - temp_min) * (ciclo_max - ciclo_min) / (temp_max - temp_min) + ciclo_min
                ciclo = max(ciclo_min, min(ciclo, ciclo_max))
                return round(ciclo)
        return round(ciclo_actual)
    except Exception as e:
        print_debug(f"Error al calcular el ciclo de trabajo: {str(e)}")
        return round(ciclo_actual)
        
def parar_ventilador(signum, frame):
    try:
        syslog.syslog(syslog.LOG_INFO, "Parando salida PWM")
        pwm.stop();
        time.sleep(1)
        # Asegurarse de que todos los buffers estén vacíos antes de salir
        sys.stdout.flush()
        sys.stderr.flush() 
        sys.exit(0)
    except Exception as e:
        print_debug(f"Error al parar el servicio: {str(e)}")

try:
    # Llama a la función para inicializar la configuración
    (intervalo_de_prueba, canal_pwm, frecuencia, temp_min, temp_max, ciclo_min, ciclo_max, histeresis, debug, as_a_service) = inicializar_configuracion()

    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    syslog.openlog(ident=script_name, facility=syslog.LOG_USER)
    syslog.syslog(syslog.LOG_INFO, f"El servicio {script_name} se está ejecutando.")
    
    # Para que se detenga el ventilador al para el script
    signal.signal(signal.SIGTERM, parar_ventilador)

    pwm.start(100)
    time.sleep(1) 

    while True:
        temp = psutil.sensors_temperatures()['cpu_thermal'][0].current
        ciclo_de_trabajo = calcular_ciclo_de_trabajo(temp, temp_min, temp_max, ciclo_min, ciclo_max, ciclo_de_trabajo, histeresis)

        if tiempo >= intervalo_de_prueba and debug is True:
            mensaje = f"La temperatura de la CPU es {temp:.2f} °C. El ciclo de trabajo es de {ciclo_de_trabajo:.0f}%"
            print_debug(mensaje)
            tiempo = 0
        else:
            tiempo += 1

        if ciclo_de_trabajo_anterior == 0 and ciclo_de_trabajo != 0:
            print_debug(f"Arrancando ventilador... (temperatura {temp:.2f}ºC)")
            pwm.change_duty_cycle(100)
            ciclo_de_trabajo_anterior = 100
            time.sleep(1)

        if ciclo_de_trabajo != ciclo_de_trabajo_anterior:
            pwm.change_duty_cycle(ciclo_de_trabajo)
            print_debug(f"Nueva temperatura: {temp:.2f}ºC. Nuevo ciclo de trabajo: {ciclo_de_trabajo:.0f}%")
            print_debug(f"Temperatura cambio anterior: {temperatura_anterior:.2f}ºC. Ciclo de trabajo anterior: {ciclo_de_trabajo_anterior:.0f}%")
            ciclo_de_trabajo_anterior = ciclo_de_trabajo
            temperatura_anterior = temp

        time.sleep(intervalo_de_prueba)

except Exception as e:
    print(f"Error general: {str(e)}")
    syslog.syslog(syslog.LOG_ERR, f"Error general: {str(e)}")