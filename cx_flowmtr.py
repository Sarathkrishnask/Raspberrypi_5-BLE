
from gpiozero import DigitalInputDevice
from time import time, sleep
import json
import logging

logging.basicConfig(filename='/home/AnarPi/Desktop/ble_gatt/blestatus.log', level=logging.INFO, format='%(asctime)s - %(message)s')

class GetFlow:
    def __init__(self):
        self.logger = logging.getLogger('BluetoothService')
        self.filepath = "/home/AnarPi/Desktop/ble_gatt/Config.json"
        self.pin_config = self.load_sensor_config()
        self.FLOW_METER_PIN = self.pin_config["water_meter"]["flow_pin"]#13#controlOptions["waterMeter_GPIO"]["inputPin"]
        self.max_flow_rate_lpm = 190  # max flow rate in liters per minute
        self.max_pressure_psi = 200  # max pressure in pounds per square inch
        
        # Flow meter pulses per gallon
        self.pulses_per_gallon = 100
        self.total_pulses = 0
        self.start_time = time()
        self.flow_rate_gpm = 0
        self.flow_rate_lpm = 0
        self.gpm_to_lpm = 3.785
        
        # Initialize the flow meter sensor
        self.sensor = DigitalInputDevice(self.FLOW_METER_PIN, pull_up=False)
        self.sensor.when_activated = self.pulse_callback
    
    def load_sensor_config(self):
        with open(self.filepath, 'r') as file:
            config = json.load(file)
            self.logger.info(config)
        return config['raspberrypi_sensors']
        
    def pulse_callback(self):
        self.total_pulses += 1

    def getflow(self):
        try:
            self.elapsed_time = time() - self.start_time
            if self.elapsed_time > 0:
                self.flow_rate_gpm = (self.total_pulses / self.pulses_per_gallon) / (self.elapsed_time / 60)
                self.flow_rate_lpm = self.flow_rate_gpm * self.gpm_to_lpm
                self.total_flow_liters = (self.total_pulses / self.pulses_per_gallon) * 3.785

#                 if self.flow_rate_lpm > self.max_flow_rate_lpm:
#                     print("Warning: Flow rate exceeds the maximum limit")
# 
#                 print(f"Flow Rate: {self.flow_rate_lpm:.2f} LPM, Total Flow: {self.total_flow_liters:.2f} Liters")
#                 print(f"Maximum Flow Rate: {self.max_flow_rate_lpm} LPM, Maximum Pressure: {self.max_pressure_psi} PSI")
#             
            sleep(0.5)
            return int(round(self.total_flow_liters))
        except Exception as e:
            self.logger.info(f"Error while try to calculate the waterflow : {e}")

            print(f"Error while running the code: {e}")

if __name__ == "__main__":
    chk_flow = GetFlow()
    while True:
        chk_flow.getflow()


