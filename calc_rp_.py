
from gpiozero import DigitalInputDevice,Button
import time
import json
import logging

logging.basicConfig(filename='/home/AnarPi/Desktop/ble_gatt/blestatus.log', level=logging.INFO, format='%(asctime)s - %(message)s')

class RPMSensor:
    def __init__(self):
        
        self.logger = logging.getLogger('BluetoothService')
        self.filepath = "/home/AnarPi/Desktop/ble_gatt/Config.json"
        self.pin_config = self.load_sensor_config()
        self.rpmpin = self.pin_config["rpm_sensor"]["rpm_pin"]#24#controlOptions["rpmSensor_GPIO"]["rpmPin"]
        self.hallpin = self.pin_config["hall_sensor"]["direction_pin"]#23 #controlOptions["hallSensor_GPIO"]["hallPin"]
        self.rpmsensor = DigitalInputDevice(self.rpmpin, pull_up=False)
        self.rpmsensor.when_activated = self._increment_count
        self.hallsensor = Button(self.hallpin, pull_up=False,bounce_time=0.1)
        self.drum_cnt = 0
        self.direction =0
        self.revolutions = 0
        self.start_time = time.time()

    def load_sensor_config(self):
        with open(self.filepath, 'r') as file:
            config = json.load(file)
            self.logger.info(config)
        return config['raspberrypi_sensors']
        
    def _increment_count(self):
        self.revolutions += 1
        self.drum_cnt +=1

        
    def update_rpm(self):       
        while True:
            try:
                if self.hallsensor.is_pressed:
                    self.direction=0

                else:
                    self.direction=1
 
                elapsed_time = time.time() - self.start_time

                rpm = (self.revolutions / elapsed_time) * 60
                self.revolutions = 0
                self.start_time = time.time()
                if self.direction==0:
                    rpm = -(rpm)
                else:
                    rpm = rpm

                return round(rpm), self.drum_cnt
            except Exception as E:
                self.logger.info(f"Error while try to calculate the RPM : {E}")
                print(E)
    
    def close(self):
        self.sensor.close()
        print(f"Sensor on pin {self.pin} closed.")



# if __name__ == "__main__":
#     
#     rpm_counter = RPMSensor()
#     while True:
#         time.sleep(1)
#         rpm,drum,directon =rpm_counter.update_rpm()
#         print(rpm,drum,directon)
    


# Set up the RPM counter on GPIO pin 21
# 
# rpm_counter = RPMSensor(21)
# 
# try:
#     while True:
#         time.sleep(1)  # Measure RPM every second
#         rpm,drum,directon = rpm_counter.update_rpm()
#         print(f"RPM: {rpm:.2f}")
# except KeyboardInterrupt:
#     print("Measurement stopped by User")
