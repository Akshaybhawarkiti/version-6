import hal
import time
import sensor
import matplotlib.pyplot as plt

ProbedLength = None
PositionData = []

Slag_x = None
Slag_End_x = None
Slag_Width = None
LimitValue = None

THRESHOLD = 2

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

    print(f">>> probed lenght = {ProbedLength}")
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

    print(f">>> probed lenght = {ProbedLength}")
    print("========================================")
    print("MOVING X UNTIL SENSOR DETECTS")
    print("========================================")

    print(">>> Starting X jog at feedrate 800")

    hal.Plus_speed("X", feedrate=1000)

    while True:

        value = sensor.get_distance()

        if value > 0.00:

            print(">>> SENSOR DETECTED")
            print(f">>> Sensor value: {value:.3f}")

            print(">>> STOPPING JOG")

            hal.block_jog()

            break

        time.sleep(0.01)

    print(">>> Sensor Detected so stopped X jog adn Slowing Down")


def PL_detect():

    global ProbedLength

    print(f">>> probed lenght = {ProbedLength}")
    print("========================================")
    print("MOVING X UNTIL Probed Lenght is detect")
    print("========================================")

    print(">>> Starting X jog at feedrate 300")

    hal.Plus_speed("X", feedrate=300)

    hal.wait_until_high_hal()

    print(f">>> probed lenght = {ProbedLength}")

    print(">>> X stopped at current position")

    time.sleep(2)

    CurrentX = hal.get_current_x_position()
    
    print("========================================")
    print(f"X Position PL is {CurrentX}")
    print("========================================")

    ProbedLength = CurrentX



UI_map = []

Slag_x = None
Slag_End_x = None
Slag_Width = None
LimitValue = None

THRESHOLD = 3
UI_MAP_DISTANCE = 0.5
FEEDRATE = 100

UI_MAP_INTERVAL = (UI_MAP_DISTANCE / FEEDRATE) * 60


def threshold_detect():

    global PositionData
    global UI_map
    global Slag_x
    global Slag_End_x
    global Slag_Width
    global LimitValue

    print("========================================")
    print("THRESHOLD DETECTION")
    print("========================================")

    PositionData = []
    UI_map = []

    previous_value = None

    next_ui_map_time = time.time()

    print(">>> Starting X- jog at feedrate 100")

    hal.Mins_speed("X", feedrate=100)

    time.sleep(1)

    # ======================================================
    # FIND SLAG START
    # ======================================================

    while True:

        value = sensor.get_distance()

        current_time = time.time()

        if current_time >= next_ui_map_time:

            UI_map.append(value)

            next_ui_map_time = current_time + UI_MAP_INTERVAL

        if previous_value is not None:

            change = abs(value - previous_value)

            if change >= THRESHOLD:

                print(">>> THRESHOLD DETECTED - Slag Found")
                print(f">>> Previous value: {previous_value:.3f}")
                print(f">>> Current value:  {value:.3f}")
                print(f">>> Change:         {change:.3f}")
                print(f">>> Threshold:      {THRESHOLD:.3f}")

                print(">>> STOPPING X JOG")

                hal.block_jog()

                time.sleep(1)

                Slag_x = hal.get_current_x_position()

                print(f">>> Slag Start X: {Slag_x:.3f} mm")

                break

        PositionData.append(value)

        previous_value = value

        time.sleep(0.01)

    # ======================================================
    # CALCULATE LIMIT VALUE
    # ======================================================

    print("========================================")
    print("CALCULATING SENSOR LIMIT")
    print("========================================")

    if len(PositionData) > 0:

        LimitValue = sum(PositionData) / len(PositionData)

    else:

        LimitValue = 0

    print(f">>> Sensor readings before slag: {len(PositionData)}")
    print(f">>> Limit Value: {LimitValue:.3f}")

    # ======================================================
    # FIND SLAG END
    # ======================================================

    print("========================================")
    print("SEARCHING FOR SLAG END")
    print("========================================")

    print(">>> Starting X- jog again at feedrate 100")

    hal.Mins_speed("X", feedrate=100)

    time.sleep(1)

    next_ui_map_time = time.time()

    while True:

        value = sensor.get_distance()

        current_time = time.time()

        if current_time >= next_ui_map_time:

            UI_map.append(value)

            next_ui_map_time = current_time + UI_MAP_INTERVAL

        if value >= LimitValue:

            print(">>> SLAG END DETECTED")
            print(f">>> Sensor value: {value:.3f}")
            print(f">>> Limit value:  {LimitValue:.3f}")

            print(">>> STOPPING X JOG")

            hal.block_jog()

            time.sleep(1)

            Slag_End_x = hal.get_current_x_position()

            print(f">>> Slag End X: {Slag_End_x:.3f} mm")

            break

        time.sleep(0.01)

    # ======================================================
    # CALCULATE SLAG WIDTH
    # ======================================================

    Slag_Width = abs(Slag_x - Slag_End_x)

    # ======================================================
    # PRINT RESULTS
    # ======================================================

    print("========================================")
    print("SLAG DETECTION COMPLETE")
    print("========================================")
    print(f">>> Slag Start X : {Slag_x:.3f} mm")
    print(f">>> Slag End X   : {Slag_End_x:.3f} mm")
    print(f">>> Slag Width   : {Slag_Width:.3f} mm")
    print(f">>> Limit Value  : {LimitValue:.3f}")
    print(f">>> UI Map Values: {len(UI_map)}")
    print("========================================")

    print(">>> UI_map:")

    for i, value in enumerate(UI_map):

        print(f">>> {i}: {value:.3f}")

    print("========================================")

    # ======================================================
    # RETURN X TO ZERO
    # ======================================================

    print(">>> Moving X to absolute position 0")

    hal.publish_absolute(x=0,feedrate=1000)

    time.sleep(1)

    hal.wait_until_idle()

    print("========================================")
    print("X RETURNED TO ABSOLUTE 0")
    print("========================================")


def plot_ui_map():

    print("========================================")
    print("PLOTTING UI MAP")
    print("========================================")

    if len(UI_map) == 0:
        print(">>> UI_map is empty")
        return

    x_values = []

    for i in range(len(UI_map)):
        x_values.append(i * 0.5)

    plt.figure()

    plt.plot(x_values, UI_map, marker="o")

    plt.xlabel("X Distance (mm)")
    plt.ylabel("Sensor Value (mm)")
    plt.title("Sensor UI Map")

    plt.grid(True)

    plt.show()

    print("========================================")
    print("UI MAP PLOT COMPLETE")
    print("========================================")



connect_hal()
move_center()
jog_detect()
PL_detect()
threshold_detect()
plot_ui_map()


print(f">>> probed length = {ProbedLength}")