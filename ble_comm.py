#!/usr/bin/python3

import dbus
from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor
from gpiozero import CPUTemperature
from gi.repository import GLib
from cx_flowmtr import *
from calc_rp_ import *
from datetime import datetime
import logging

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000
logging.basicConfig(filename='/home/AnarPi/Desktop/ble_gatt/blestatus.log', level=logging.INFO, format='%(asctime)s - %(message)s')


class IstradaAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("pi5_ble")
        
        self.include_tx_power = True

class IstradaService(Service):
    ISTRADA_SVC_UUID = "20bb0d58-b635-4113-9db7-f4e4e37e3985"

    def __init__(self, index):
        rpm_sensor = RPMSensor()
        
        self.logger = logging.getLogger('BluetoothService')
        self.bus = dbus.SystemBus()
        self.add_service_status_changed_handler()
        Service.__init__(self,index, self.ISTRADA_SVC_UUID, True)
        self.add_characteristic(RpmCharacteristic(self,rpm_sensor))
        self.add_characteristic(DrumCharacteristic(self,rpm_sensor))
        self.add_characteristic(FlowCharacteristic(self))
        self.add_characteristic(TimeCharacteristic(self))
        self.add_characteristic(FileReceiveCharacteristic(self))

    def add_service_status_changed_handler(self):
        self.bus.add_signal_receiver(
            self.on_properties_changed,
            dbus_interface="org.freedesktop.DBus.Properties",
            signal_name="PropertiesChanged",
            arg0="org.bluez.Device1",
            path_keyword="path"
        )

    def on_properties_changed(self, interface, changed, invalidated, path):
        if "Connected" in changed:
            connected = changed["Connected"]
            if connected:
                self.logger.info(f"Device connected: {path}")
                print(f"Device connected: {path}")
            else:
                self.logger.info(f"Device disconnected: {path}")
                print(f"Device disconnected: {path}")

# 
class RpmCharacteristic(Characteristic):
    RPM_CHARACTERISTIC_UUID = "128a6cdd-56fe-4859-881d-216088fc587d"

    def __init__(self, service,rpm_char):
        self.notifying = False
        
        self.currRpm = 0
        self.revolution = 0
        self.rpm_char = rpm_char
        Characteristic.__init__(
                self, self.RPM_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(RpmDescriptor(self))


    def ReadValue(self, options):
        self.currRpm,_= self.rpm_char.update_rpm()
        value =str(self.currRpm)
        value = bytearray([dbus.Byte(c.encode()) for c in value])
        print(value)
        return value


class RpmDescriptor(Descriptor):
    RPM_DESCRIPTOR_UUID = "2901"
    RPM_DESCRIPTOR_VALUE = "Total Rpm"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.RPM_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.RPM_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return bytearray(value)


class DrumCharacteristic(Characteristic):
    DRUM_CHARACTERISTIC_UUID = "a86b7763-800f-404e-b965-74e6a19ab4f9"

    def __init__(self, service,rev_char):
        self.notifying = False
        self.rev_char = rev_char
        Characteristic.__init__(
                self, self.DRUM_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(DrumDescriptor(self))

    def ReadValue(self, options):
        _,self.revolution = self.rev_char.update_rpm()
        value = str(self.revolution)
        value = bytearray([dbus.Byte(c.encode()) for c in value])
        print(value)
        return value


class DrumDescriptor(Descriptor):
    DRUM_DESCRIPTOR_UUID = "2901"
    DRUM_DESCRIPTOR_VALUE = "Total Drum Rotation Count"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.DRUM_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.DRUM_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))
        return bytearray(value)


class FlowCharacteristic(Characteristic):
    FLOW_CHARACTERISTIC_UUID = "4190a0c9-dcea-400d-9017-926cfa3b3a9c"
    def __init__(self, service):
        self.notifying = False
        self.flow = GetFlow()
        Characteristic.__init__(
                self, self.FLOW_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(FlowDescriptor(self))


    def ReadValue(self, options):

        value =str(self.flow.getflow())
        value = bytearray([dbus.Byte(c.encode()) for c in value])
        print(value)
        return value


class FlowDescriptor(Descriptor):
    FLOW_DESCRIPTOR_UUID = "2901"
    FLOW_DESCRIPTOR_VALUE = "Total Liquid Flow"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.FLOW_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.FLOW_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return bytearray(value)


class TimeCharacteristic(Characteristic):
    UART_RX_CHARACTERISTIC_UUID ="784ab4cc-6f3f-42e1-9bbe-5d20619ee0f1"
    def __init__(self,service):
        Characteristic.__init__(self, self.UART_RX_CHARACTERISTIC_UUID,
                                ['write'], service)
        self.add_descriptor(TimeDescriptor(self))

    def WriteValue(self, value, options):
        date_format = "%Y-%m-%d %H:%M:%S"
        print('remote: {}'.format(bytearray(value).decode()))
        try:
            # Command to set the system date and time
            new_time = bytearray(value).decode()
            date_time_obj = datetime.strptime(new_time, date_format)
            command = ['sudo', 'date', '--set', new_time]

            # Execute the command
            result = subprocess.run(command, capture_output=True, text=True)

            # Check for errors
            if result.returncode != 0:
                print(f"Error setting date: {result.stderr}")
            else:
                print(f"Date set successfully: {new_time}")
        except Exception as e:
            print(f"An error occurred: {e}")
            
            
class TimeDescriptor(Descriptor):
    TIME_DESCRIPTOR_UUID = "2901"
    TIME_DESCRIPTOR_VALUE = "Raspberrypi Time Update"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.TIME_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.TIME_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return bytearray(value)



class FileReceiveCharacteristic(Characteristic):
    FILE_RECEIVE_UUID = "1827a456-3f13-4bbf-ba10-dbb4ecc5d8fd"

    def __init__(self, service):
        Characteristic.__init__(
            self, self.FILE_RECEIVE_UUID,
            ["write"], service)
        self.add_descriptor(FirmwareDescriptor(self))

    def WriteValue(self, value, options):
        # Process received file data here
        file_data = bytes(value)

        # Example: Save received file to a local file
        with open("iStrada.zip", "wb") as file:
            file.write(file_data)

        print("Received file saved.")

        
class FirmwareDescriptor(Descriptor):
    FIRMWARE_DESCRIPTOR_UUID = "2901"
    FIRMWARE_DESCRIPTOR_VALUE = "Firmware Update"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.FIRMWARE_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.FIRMWARE_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return bytearray(value)


app = Application()
app.add_service(IstradaService(0))
app.register()
# 
adv = IstradaAdvertisement(0)
adv.register()
# 
try:
    app.run()
except KeyboardInterrupt:
    app.quit()


# class BLEApplication(Application):
#     def __init__(self):
#         Application.__init__(self)
#         self.service = IstradaService(0)
#         self.add_service(self.service)
#         
#         
# 
#     def run(self):
#         self.mainloop = GLib.MainLoop()
#         self.mainloop.run()
# 
#     def quit(self):
#         self.mainloop.quit()
# 
#     def setup(self):
#         self.register()
#         adv = IstradaAdvertisement(0)
#         adv.register()

