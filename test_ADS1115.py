import board
import busio
import time
i2c = busio.I2C(board.SCL, board.SDA)
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

ads = ADS.ADS1115(i2c)

while True:
    chan = AnalogIn(ads, ADS.P0)
    print("\rChannel 0: ", chan.value, chan.voltage, end="")
    time.sleep(0.2)