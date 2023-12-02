import sys
from rpi_hardware_pwm import HardwarePWM
 
def set_pwm(pwm_channel, frequency, duty_cycle):
    pwm = HardwarePWM(pwm_channel, frequency)
    pwm.start(duty_cycle)
    input("Presiona Enter para detener el PWM...")
    pwm.stop()
 
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python pwm_generator.py <canal_pwm> <frecuencia> <ciclo_de_trabajo>")
        sys.exit(1)
 
    pwm_channel = int(sys.argv[1])
    frequency = float(sys.argv[2])
    duty_cycle = float(sys.argv[3])
 
    try:
        set_pwm(pwm_channel, frequency, duty_cycle)
    except KeyboardInterrupt:
        pass