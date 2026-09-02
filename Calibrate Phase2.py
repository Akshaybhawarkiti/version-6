import hal
import time
import sensor
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
import csv

ProbedLength = None
PositionData = []

Slag_x = None
Slag_End_x = None
Slag_Width = None
LimitValue = None

THRESHOLD = 2

Layer1 = []
Layer2 = []
Layer3 = []
Layer4 = []

ANGLE_STEP = 0.5
ROTATION_FEEDRATE = 1440
ROTATION_RPM = 4


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

        if value is None:
            continue

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

        if value is None:
            continue

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

        if value is None:
            continue

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

    # # ======================================================
    # # RETURN X TO ZERO
    # # ======================================================

    # print(">>> Moving X to absolute position 0")

    # hal.publish_absolute(x=0,feedrate=1000)

    # time.sleep(1)

    # hal.wait_until_idle()

    # print("========================================")
    # print("X RETURNED TO ABSOLUTE 0")
    # print("========================================")


def plot_ui_map():

    print("========================================")
    print("PLOTTING UI MAP")
    print("========================================")

    if len(UI_map) == 0:
        print(">>> UI_map is empty")
        return

    # ======================================================
    # FILTER ZERO VALUES
    # ======================================================

    print(">>> Checking UI_map for zero values...")

    for i in range(len(UI_map)):

        if UI_map[i] == 0.0:

            if i > 0:

                print(
                    f">>> Zero value found at index {i}. "
                    f"Replacing {UI_map[i]:.3f} "
                    f"with previous value {UI_map[i - 1]:.3f}"
                )

                UI_map[i] = UI_map[i - 1]

            else:

                print(
                    ">>> Zero value found at index 0. "
                    "No previous value available."
                )

    # ======================================================
    # CREATE X VALUES
    # ======================================================

    x_values = []

    for i in range(len(UI_map)):
        x_values.append(i * 0.5)

    # ======================================================
    # PLOT
    # ======================================================

    fig, ax = plt.subplots(figsize=(9, 5), dpi=110)

    # Smooth curve through the recorded samples (visual only,
    # underlying data/markers below are the real readings)
    if len(x_values) >= 4:

        spline = make_interp_spline(x_values, UI_map, k=3)

        x_smooth = np.linspace(x_values[0], x_values[-1], len(x_values) * 20)
        y_smooth = spline(x_smooth)

        ax.plot(x_smooth, y_smooth, color="#1f77b4", linewidth=2, zorder=2)

    else:

        ax.plot(x_values, UI_map, color="#1f77b4", linewidth=2, zorder=2)

    ax.plot(
        x_values, UI_map,
        marker="o", markersize=5, linestyle="None",
        color="#1f77b4", markerfacecolor="white", markeredgewidth=1.4,
        zorder=3, label="Sensor Reading"
    )

    # ======================================================
    # CONNECT LAST READING DOWN TO THE LIMIT VALUE
    # ======================================================
    # The sample that actually crossed the limit (slag end) is not
    # captured in UI_map since it only records on a fixed interval,
    # so the line otherwise stops short. Draw the missing segment.

    if LimitValue is not None:

        ax.plot(
            [x_values[-1], x_values[-1]],
            [UI_map[-1], LimitValue],
            color="#1f77b4", linewidth=2, linestyle="--", zorder=2
        )

        ax.axhline(
            LimitValue, color="#d62728", linestyle="--", linewidth=1.3,
            zorder=1, label=f"Limit Value ({LimitValue:.2f} mm)"
        )

    ax.set_xlabel("X Distance (mm)")
    ax.set_ylabel("Sensor Value (mm)")
    ax.set_title("Sensor UI Map", fontsize=13, fontweight="bold")

    ax.grid(True, alpha=0.4)
    ax.legend(loc="best", frameon=True)

    fig.tight_layout()

    plt.show()

    print("========================================")
    print("UI MAP PLOT COMPLETE")
    print("========================================")


def data_collector():

    global Layer1
    global Layer2
    global Layer3
    global Layer4

    print("========================================")
    print("DATA COLLECTION")
    print("========================================")

    print(f">>> Slag End X: {Slag_End_x:.3f} mm")
    print(f">>> Slag Width: {Slag_Width:.3f} mm")

    # ======================================================
    # MOVE X TO SLAG END POSITION
    # ======================================================

    print("========================================")
    print("MOVING X TO SLAG END POSITION")
    print("========================================")

    print(f">>> Moving X to absolute position {Slag_End_x:.3f} mm")

    hal.publish_absolute(x=Slag_End_x,feedrate=1000)

    time.sleep(1)

    hal.wait_until_idle()

    print(">>> X reached Slag End position")

    # ======================================================
    # CALCULATE CREEP DISTANCE
    # ======================================================

    CreepDistance = Slag_Width / 4

    print("========================================")
    print("CREEP DISTANCE")
    print("========================================")

    print(f">>> Slag Width: {Slag_Width:.3f} mm")
    print(f">>> Creep Distance: {CreepDistance:.3f} mm")

    # ======================================================
    # SENSOR SAMPLING SETTINGS
    # ======================================================

    angle_step = ANGLE_STEP

    total_samples = int(360 / angle_step)

    rotation_time = 60 / ROTATION_RPM

    sample_interval = rotation_time / total_samples

    print("========================================")
    print("ROTATION SETTINGS")
    print("========================================")

    print(f">>> Rotation: 360 degrees")
    print(f">>> Rotation speed: {ROTATION_RPM} RPM")
    print(f">>> Rotation time: {rotation_time:.3f} seconds")
    print(f">>> Angle step: {angle_step:.3f} degrees")
    print(f">>> Samples per layer: {total_samples}")
    print(f">>> Sensor interval: {sample_interval:.6f} seconds")
    print(f">>> Sensor interval: {sample_interval * 1000:.3f} ms")

    # ======================================================
    # CLEAR OLD DATA
    # ======================================================

    Layer1 = []
    Layer2 = []
    Layer3 = []
    Layer4 = []

    # ======================================================
    # LAYER 1
    # ======================================================

    print("========================================")
    print("STARTING LAYER 1")
    print("========================================")

    hal.publish_gcode_hal2(x=360,feedrate=ROTATION_FEEDRATE)

    start_time = time.time()

    while len(Layer1) < total_samples:

        value = sensor.get_distance()

        if value is None:
            continue

        Layer1.append(value)

        next_sample_time = start_time + (len(Layer1) * sample_interval)

        while time.time() < next_sample_time:
            time.sleep(0.001)

    print(f">>> Layer 1 complete")
    print(f">>> Values collected: {len(Layer1)}")

    hal.wait_until_idle2()

    # ======================================================
    # CREEP TO LAYER 2
    # ======================================================

    print("========================================")
    print("MOVING TO LAYER 2")
    print("========================================")

    hal.publish_gcode(x=CreepDistance,feedrate=1000)

    time.sleep(1)

    hal.wait_until_idle()

    # ======================================================
    # LAYER 2
    # ======================================================

    print("========================================")
    print("STARTING LAYER 2")
    print("========================================")

    hal.publish_gcode_hal2(x=360,feedrate=ROTATION_FEEDRATE)

    start_time = time.time()

    while len(Layer2) < total_samples:

        value = sensor.get_distance()

        if value is None:
            continue

        Layer2.append(value)

        next_sample_time = start_time + (
            len(Layer2) * sample_interval
        )

        while time.time() < next_sample_time:
            time.sleep(0.001)

    print(f">>> Layer 2 complete")
    print(f">>> Values collected: {len(Layer2)}")

    hal.wait_until_idle2()

    # ======================================================
    # CREEP TO LAYER 3
    # ======================================================

    print("========================================")
    print("MOVING TO LAYER 3")
    print("========================================")

    hal.publish_gcode(x=CreepDistance,feedrate=1000)

    time.sleep(1)

    hal.wait_until_idle()

    # ======================================================
    # LAYER 3
    # ======================================================

    print("========================================")
    print("STARTING LAYER 3")
    print("========================================")

    hal.publish_gcode_hal2(x=360,feedrate=ROTATION_FEEDRATE)

    start_time = time.time()

    while len(Layer3) < total_samples:

        value = sensor.get_distance()

        if value is None:
            continue

        Layer3.append(value)

        next_sample_time = start_time + (
            len(Layer3) * sample_interval
        )

        while time.time() < next_sample_time:
            time.sleep(0.001)

    print(f">>> Layer 3 complete")
    print(f">>> Values collected: {len(Layer3)}")

    hal.wait_until_idle2()

    # ======================================================
    # CREEP TO LAYER 4
    # ======================================================

    print("========================================")
    print("MOVING TO LAYER 4")
    print("========================================")

    hal.publish_gcode(x=CreepDistance,feedrate=1000)

    time.sleep(1)

    hal.wait_until_idle()

    # ======================================================
    # LAYER 4
    # ======================================================

    print("========================================")
    print("STARTING LAYER 4")
    print("========================================")

    hal.publish_gcode_hal2(x=360,feedrate=ROTATION_FEEDRATE)

    start_time = time.time()

    while len(Layer4) < total_samples:

        value = sensor.get_distance()

        if value is None:
            continue

        Layer4.append(value)

        next_sample_time = start_time + (
            len(Layer4) * sample_interval
        )

        while time.time() < next_sample_time:
            time.sleep(0.001)

    print(f">>> Layer 4 complete")
    print(f">>> Values collected: {len(Layer4)}")

    hal.wait_until_idle2()

    # ======================================================
    # PRINT ALL LAYER DATA
    # ======================================================

    print("========================================")
    print("ALL LAYERS COMPLETE")
    print("========================================")

    print(f">>> Layer 1 values: {len(Layer1)}")
    print(f">>> Layer 2 values: {len(Layer2)}")
    print(f">>> Layer 3 values: {len(Layer3)}")
    print(f">>> Layer 4 values: {len(Layer4)}")

    print("========================================")
    print("LAYER DATA")
    print("========================================")

    for i in range(total_samples):

        angle = i * angle_step

        print(
            f">>> Angle: {angle:.1f}° | "
            f"Layer1: {Layer1[i]:.3f} | "
            f"Layer2: {Layer2[i]:.3f} | "
            f"Layer3: {Layer3[i]:.3f} | "
            f"Layer4: {Layer4[i]:.3f}"
        )

    # ======================================================
    # SAVE CSV
    # ======================================================

    print("========================================")
    print("SAVING CSV")
    print("========================================")

    with open("UI_Map_Layers.csv", "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "angle",
            "layer1",
            "layer2",
            "layer3",
            "layer4"
        ])

        for i in range(total_samples):

            angle = i * angle_step

            writer.writerow([
                angle,
                Layer1[i],
                Layer2[i],
                Layer3[i],
                Layer4[i]
            ])

    print(">>> CSV saved as UI_Map_Layers.csv")

    # ======================================================
    # RETURN X TO ABSOLUTE ZERO
    # ======================================================

    print("========================================")
    print("RETURNING X TO ABSOLUTE 0")
    print("========================================")

    hal.publish_absolute(x=0,feedrate=1000)

    time.sleep(1)

    hal.wait_until_idle()

    print("========================================")
    print("DATA COLLECTION COMPLETE")
    print("X RETURNED TO ABSOLUTE 0")
    print("========================================")


def plot_heat_gradient_3d():

    global Layer1
    global Layer2
    global Layer3
    global Layer4

    print("========================================")
    print("FILTERING LAYER DATA")
    print("========================================")

    # ======================================================
    # FILTER ONLY THE FOUR LAYER ARRAYS
    # DO NOT TOUCH ANGLE DATA
    # ======================================================

    layer_arrays = [
        ("Layer1", Layer1),
        ("Layer2", Layer2),
        ("Layer3", Layer3),
        ("Layer4", Layer4)
    ]

    for layer_name, layer_data in layer_arrays:

        for i in range(len(layer_data)):

            # ONLY replace an ABSOLUTE numeric zero
            if layer_data[i] == 0.0:

                if i > 0:

                    previous_value = layer_data[i - 1]

                    print(
                        f">>> {layer_name}: "
                        f"Zero found at index {i}, "
                        f"replacing with previous value "
                        f"{previous_value:.4f}"
                    )

                    layer_data[i] = previous_value

                else:

                    print(
                        f">>> {layer_name}: "
                        f"Zero found at index 0. "
                        f"No previous layer value available."
                    )

    print(">>> Layer zero filtering complete")

    # ======================================================
    # CHECK DATA
    # ======================================================

    if len(Layer1) == 0:
        print(">>> Layer1 is empty")
        return

    # ======================================================
    # CREATE DATA MATRIX
    # ======================================================

    layers = [
        Layer1,
        Layer2,
        Layer3,
        Layer4
    ]

    layer_names = [
        "Layer 1",
        "Layer 2",
        "Layer 3",
        "Layer 4"
    ]

    # ======================================================
    # CREATE ANGLE VALUES
    # ======================================================

    angles = []

    for i in range(len(Layer1)):
        angles.append(i * ANGLE_STEP)

    # ======================================================
    # HEAT / GRADIENT MAP
    # ======================================================

    print("========================================")
    print("PLOTTING HEAT / GRADIENT MAP")
    print("========================================")

    plt.figure()

    plt.imshow(
        layers,
        aspect="auto",
        extent=[
            0,
            360,
            4,
            1
        ],
        origin="upper"
    )

    plt.colorbar(label="Sensor Value")

    plt.xlabel("Rotation Angle (degrees)")
    plt.ylabel("Layer")
    plt.title("Cylinder Sensor Heat / Gradient Map")

    plt.yticks(
        [1, 2, 3, 4],
        layer_names
    )

    plt.xticks(
        range(0, 361, 30)
    )

    plt.show()

    # ======================================================
    # 3D MAP
    # ======================================================

    print(">>> Creating 3D sensor map")

    fig = plt.figure()

    ax = fig.add_subplot(
        111,
        projection="3d"
    )

    for layer_index, layer_data in enumerate(layers):

        x_values = angles

        y_values = [
            layer_index + 1
        ] * len(layer_data)

        z_values = layer_data

        ax.plot(
            x_values,
            y_values,
            z_values
        )

    ax.set_xlabel("Rotation Angle (degrees)")
    ax.set_ylabel("Layer")
    ax.set_zlabel("Sensor Value")

    ax.set_title("3D Cylinder Sensor Map")

    ax.set_yticks(
        [1, 2, 3, 4]
    )

    plt.show()

    print("========================================")
    print("HEAT / GRADIENT MAP COMPLETE")
    print("3D MAP COMPLETE")
    print("========================================")
    


connect_hal()
move_center()
jog_detect()
PL_detect()
threshold_detect()
plot_ui_map()
data_collector()
plot_heat_gradient_3d()
print(f">>> probed length = {ProbedLength}")