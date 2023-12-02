import psutil
import time
 
def get_cpu_temperature():
    try:
        temperature = psutil.sensors_temperatures()['cpu_thermal'][0].current
        return temperature
    except Exception as e:
        print(f"Error al obtener la temperatura de la CPU: {e}")
        return None
 
def main():
    try:
        while True:
            temperature = get_cpu_temperature()
 
            if temperature is not None:
                print(f"Temperatura de la CPU: {temperature}°C")
 
            time.sleep(5)
 
    except KeyboardInterrupt:
        pass
 
if __name__ == "__main__":
    main()