import board
import busio
import time
i2c = busio.I2C(board.SCL, board.SDA)
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

channels = [ADS.P0, ADS.P1, ADS.P2, ADS.P3]

class KnobInput:
    def __init__(self, cid=0):
        self.ads = ADS.ADS1115(i2c)
        self.channel = AnalogIn(self.ads, channels[cid])
        
        self.last_voltage = 0
        self.threshold = 3.3 * 0.01
        self.poll_interval = 0.1  # seconds
        self.last_time = None

    def read_knob(self, i_channel):
        return channel.value, channel.voltage