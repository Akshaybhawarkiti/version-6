import hal
import time

hal.search_connect()    
hal.reset()
time.sleep(1)
hal.reset2()
time.sleep(1)
hal.unlock()
time.sleep(1)
hal.unlock2()

print("Starting Y+ jog...")
hal.Mins_speed("X", feedrate=500)

time.sleep(1)

print("Stopping Y jog...")
hal.block_jog()