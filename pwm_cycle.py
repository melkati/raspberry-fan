from rpi_hardware_pwm import HardwarePWM
import time

# Configuración
canal_pwm = 0
frecuencia = 25000
pwm = HardwarePWM(canal_pwm, frecuencia)

# Configuración de PWM
pwm.start(100)
time.sleep(11) 


try:
    while True:
        # Incrementa el ciclo de trabajo del 0% al 100%
        for duty_cycle in range(0, 101, 5):
            pwm.change_duty_cycle(duty_cycle)
            time.sleep(5 / 20)  # Espera 5 segundos divididos por el número de pasos

        # Decrementa el ciclo de trabajo del 100% al 0%
        for duty_cycle in range(100, -1, -5):
            pwm.change_duty_cycle(duty_cycle)
            time.sleep(5 / 20)  # Espera 5 segundos divididos por el número de pasos

except KeyboardInterrupt:
    pass

finally:
    # Detener el PWM y limpiar los pines
    pwm.stop()