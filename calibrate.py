import hal
import time
import sensor

def connect_hal():
    hal.search_connect()
    hal.reset()
    time.sleep(1)
    hal.reset2()
    time.sleep(1)
    hal.unlock()
    time.sleep(1)
    hal.unlock2()


def move_center():

    print("========================================")
    print("MOVING TO CENTER")
    print("========================================")

    print(">>> Homing X, Z, Y axes...")
    hal.home_all()

    time.sleep(1)

    print(">>> Waiting for homing to complete...")
    hal.wait_until_idle()

    print(">>> Homing completed")

    print(">>> Moving Y axis 370 mm...")
    sensor_center = 372 - 75
    hal.publish_gcode(y=sensor_center,feedrate=1000)
    time.sleep(1)
    print(">>> Waiting for Y movement to complete...")
    hal.wait_until_idle()

    print("========================================")
    print("CENTER POSITION REACHED")
    print(f"Y position moved {sensor_center} mm")
    print("========================================")



def jog_detect():

    print("========================================")
    print("MOVING X UNTIL SENSOR DETECTS")
    print("========================================")

    print(">>> Starting X jog at feedrate 800")

    hal.Plus_speed("X", feedrate=800)

    while True:

        value = sensor.get_distance()

        if value > 0.00:

            print(">>> SENSOR DETECTED")
            print(f">>> Sensor value: {value:.3f}")

            print(">>> STOPPING JOG")

            hal.block_jog()

            break

        time.sleep(0.01)

    print(">>> X stopped at current position")

    print(">>> Waiting 10 seconds...")

    CurrentX = hal.get_current_x_position()
    
    print("========================================")
    print(f"X Position is {CurrentX}")
    print("========================================")

    time.sleep(10)

    print(">>> Moving X to absolute position 0")

    hal.publish_absolute(x=0,feedrate=1000)
    time.sleep(1) 
    hal.wait_until_idle()

    print("========================================")
    print("X RETURNED TO ABSOLUTE 0")
    print("========================================")


def PL_detect():

    print("========================================")
    print("MOVING X UNTIL Probed Lenght is detect")
    print("========================================")

    print(">>> Starting X jog at feedrate 300")

    hal.Plus_speed("X", feedrate=300)

    hal.wait_until_high(6)

    print(">>> X stopped at current position")

    time.sleep(2)

    CurrentX = hal.get_current_x_position()
    
    print("========================================")
    print(f"X Position PL is {CurrentX}")
    print("========================================")

    time.sleep(5)

    print(">>> Moving X to absolute position 0")

    hal.publish_absolute(x=0,feedrate=1000)
    time.sleep(1) 
    hal.wait_until_idle()

    print("========================================")
    print("X RETURNED TO ABSOLUTE 0")
    print("========================================")



connect_hal()
move_center()
jog_detect()