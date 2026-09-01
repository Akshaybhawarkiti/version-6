import serial
import serial.tools.list_ports
import time
import csv
import os


SERIAL_PORT = None
SERIAL_PORT2 = None
BAUD_RATE = 115200

ser = None
ser2 = None

POSITION_FILE = "last_position.csv"


def search_connect():
    global SERIAL_PORT
    global SERIAL_PORT2
    global ser
    global ser2

    SERIAL_PORT = None
    SERIAL_PORT2 = None
    ser = None
    ser2 = None

    print("========================================")
    print("Searching for FluidNC controllers...")
    print("Waiting for MASTER and CHUCK...")
    print("========================================")

    while SERIAL_PORT is None or SERIAL_PORT2 is None:

        ports = serial.tools.list_ports.comports()

        if not ports:
            print("No COM ports found.")
            time.sleep(1)
            continue

        for port in ports:

            port_name = port.device

            # Skip already identified ports
            if port_name == SERIAL_PORT:
                continue

            if port_name == SERIAL_PORT2:
                continue

            print()
            print(f"Checking {port_name}...")

            # ========================================
            # OPEN COM PORT
            # ========================================

            try:

                connection = serial.Serial(
                    port=port_name,
                    baudrate=BAUD_RATE,
                    timeout=0.1,
                    write_timeout=0.5
                )

            except Exception as e:

                print(f"Could not open {port_name}.")
                print(f"Skipping {port_name}: {e}")

                continue

            # ========================================
            # WAIT FOR FLUIDNC STARTUP TO FINISH
            # ========================================

            time.sleep(2)


            # ========================================
            # CLEAR ALL STARTUP MESSAGES
            # ========================================

            connection.reset_input_buffer()

            # ========================================
            # PORT OPENED
            # ========================================

            try:

                connection.reset_input_buffer()

                connection.write(b"$I\n")

                print(f">>> Sent $I to {port_name}")

            except Exception as e:

                print(f"Communication error on {port_name}: {e}")

                try:
                    connection.close()
                except:
                    pass

                continue

            # ========================================
            # WAIT MAXIMUM 2 SECONDS
            # ========================================

            response = ""

            start_time = time.time()

            while (time.time() - start_time) < 2.0:

                try:

                    if connection.in_waiting:

                        while connection.in_waiting:

                            line = connection.readline().decode(
                                errors="ignore"
                            ).strip()

                            if line:

                                print(
                                    f"<<< {port_name}: {line}"
                                )

                                response += line + "\n"

                except Exception as e:

                    print(
                        f"Read error on {port_name}: {e}"
                    )

                    break

                # ====================================
                # STOP IMMEDIATELY IF IDENTIFIED
                # ====================================

                if "MSG:Machine: MASTER" in response:
                    break

                if "MSG:Machine: CHUCK" in response:
                    break

                time.sleep(0.01)

            # ========================================
            # MASTER FOUND
            # ========================================

            if "MSG:Machine: MASTER" in response:

                SERIAL_PORT = port_name
                ser = connection

                print("========================================")
                print(f"MASTER FOUND on {SERIAL_PORT}")
                print(f"SERIAL_PORT = {SERIAL_PORT}")
                print("========================================")

                continue

            # ========================================
            # CHUCK FOUND
            # ========================================

            if "MSG:Machine: CHUCK" in response:

                SERIAL_PORT2 = port_name
                ser2 = connection

                print("========================================")
                print(f"CHUCK FOUND on {SERIAL_PORT2}")
                print(f"SERIAL_PORT2 = {SERIAL_PORT2}")
                print("========================================")

                continue

            # ========================================
            # NOTHING RECEIVED IN 2 SECONDS
            # ========================================

            print(
                f"No response from {port_name} "
                f"within 2 seconds."
            )

            print(f"Skipping {port_name}...")

            try:
                connection.close()
            except:
                pass

        # ============================================
        # BOTH FOUND
        # ============================================

        if SERIAL_PORT is not None and SERIAL_PORT2 is not None:

            print()
            print("========================================")
            print("BOTH CONTROLLERS FOUND")
            print("========================================")
            print(f"MASTER = {SERIAL_PORT}")
            print(f"CHUCK  = {SERIAL_PORT2}")
            print("========================================")

            return ser, ser2

        # ============================================
        # SOMETHING STILL MISSING
        # ============================================

        print()
        print("========================================")

        if SERIAL_PORT is None:
            print("MASTER not found.")

        if SERIAL_PORT2 is None:
            print("CHUCK not found.")

        print("Searching again...")

        print("========================================")

        time.sleep(1)

def connect():
    global ser

    print(f"Connecting to {SERIAL_PORT}...")

    ser = serial.Serial(
        port=SERIAL_PORT,
        baudrate=BAUD_RATE,
        timeout=1
    )

    time.sleep(2)
    ser.reset_input_buffer()

    print("Connected.")

    return ser


def connect2():
    global ser2

    print(f"Connecting to {SERIAL_PORT2}...")

    ser2 = serial.Serial(
        port=SERIAL_PORT2,
        baudrate=BAUD_RATE,
        timeout=1
    )

    time.sleep(2)
    ser2.reset_input_buffer()

    print("Connected.")

    return ser2



def save_position(x, y, z):

    file_exists = os.path.exists(POSITION_FILE)

    with open(POSITION_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["X", "Y", "Z"])

        writer.writerow([x, y, z])



def wait_until_idle():
    global ser

    while True:
        ser.write(b"?\n")

        time.sleep(0.1)

        while ser.in_waiting:
            response = ser.readline().decode(errors="ignore").strip()

            if response:
                print("<<<", response)

                # ==================================================
                # READ AND SAVE MACHINE POSITION
                # ==================================================

                if "MPos:" in response:

                    position_part = response.split("MPos:")[1].split("|")[0]
                    values = position_part.split(",")

                    if len(values) >= 3:

                        x = float(values[0])
                        y = float(values[1])
                        z = float(values[2])

                        print(
                            f'POSITION: '
                            f'X={x:.3f}, '
                            f'Y={y:.3f}, '
                            f'Z={z:.3f}, '
                        )

                        save_position(x, y, z)

                # ==================================================
                # CHECK FOR IDLE
                # ==================================================

                if response.startswith("<Idle"):
                    print("Machine is IDLE.")
                    return

        time.sleep(0.1)



def only_idle():
    global ser

    while True:
        ser.write(b"?\n")

        time.sleep(0.1)

        while ser.in_waiting:
            response = ser.readline().decode(errors="ignore").strip()

            if response:
                print("<<<", response)

                if response.startswith("<Idle"):
                    print("Machine is IDLE.")
                    return

        time.sleep(0.1)




def recover_position(upmax, x_retract):
    global ser

    if not os.path.exists(POSITION_FILE):
        print("No saved position found.")
        return

    with open(POSITION_FILE, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        last_row = None
        for row in reader:
            last_row = row

        if last_row:
            x, y, z = map(float, last_row)
            print(f"Recovering to position: X={x}, Y={y}, Z={z}")

            neg_x = -x + x_retract
            neg_y = -y + upmax
            neg_z = -z

            publish_gcode(x=neg_x, y=neg_y,feedrate=1000)
            only_idle()
            publish_gcode(z=neg_z,feedrate=1000)
            only_idle()
            home_all()

        else:
            print("No saved position found.")



def clear_position_file():

    with open(POSITION_FILE, "w", newline="") as file:
        pass

    print("Position file cleared.")



def unlock():
    global ser

    ser.write(b"$X\n")
    time.sleep(0.5)

    while ser.in_waiting:
        print("<<<", ser.readline().decode(errors="ignore").strip())


def unlock2():
    global ser2

    ser2.write(b"$X\n")
    time.sleep(0.5)

    while ser2.in_waiting:
        print("<<<", ser2.readline().decode(errors="ignore").strip())

#################################################################################################

def Plus(axis):
    global ser

    gcode = f"$J=G91 {axis}400 F1000"
    print(f">>> Sending: {gcode}")
    ser.write((gcode + "\n").encode())
    time.sleep(0.05)



def Mins(axis):
    global ser

    gcode = f"$J=G91 {axis}-400 F1000"   #$J=G91 X40 F1000
    print(f">>> Sending: {gcode}")
    ser.write((gcode + "\n").encode())
    time.sleep(0.05)


def Plus_speed(axis, feedrate=1000):
    global ser

    gcode = f"$J=G91 {axis}400 F{feedrate}"
    print(f">>> Sending: {gcode}")
    ser.write((gcode + "\n").encode())
    time.sleep(0.05)


def Mins_speed(axis, feedrate=1000):
    global ser

    gcode = f"$J=G91 {axis}-400 F{feedrate}"
    print(f">>> Sending: {gcode}")
    ser.write((gcode + "\n").encode())
    time.sleep(0.05)


def block_jog():
    global ser

    print(f">>> Sending: Jog stop x85")
    ser.write(b'\x85')
    time.sleep(0.5)

####################################################################################################

def Plus_hal2(axis):
    global ser2

    gcode = f"$J=G91 {axis}3600 F1000"
    print(f">>> Sending to hal2: {gcode}")
    ser2.write((gcode + "\n").encode())
    time.sleep(0.5)

def block_jog_hal2():
    global ser2

    print(f">>> Sending: Jog stop x85 to Hal2")
    ser2.write(b'\x85')
    time.sleep(0.5)

####################################################################################################

def feed_hold():
    global ser

    if ser is None:
        print("Feed hold requested, but not connected.")
        return

    ser.write(b"!")
    print(">>> Feed Hold (!)")


def reset():
    global ser

    if ser is None:
        print("Reset requested, but not connected.")
        return

    ser.write(b"\x18")
    print(">>> Soft Reset (0x18)")


def reset2():
    global ser

    if ser2 is None:
        print("Reset requested, but not connected.")
        return

    ser2.write(b"\x18")
    print(">>> Soft Reset (0x18)")


def TurnON(pin):
    global ser

    if ser is None:
        print("Turn ON requested, but not connected.")
        return

    gcode = f"M64 P{pin}"

    print(f">>> Sending: {gcode}")

    ser.write((gcode + "\n").encode())


def TurnOFF(pin):
    global ser

    if ser is None:
        print("Turn OFF requested, but not connected.")
        return

    gcode = f"M65 P{pin}"

    print(f">>> Sending: {gcode}")

    ser.write((gcode + "\n").encode())



def disconnect():
    global ser

    if ser is not None:
        ser.close()
        ser = None


def home_all():
    """Home X, then Z, then Y."""

    global ser

    for axis in ["X", "Y"]:
            print(f">>> Homing {axis}")
            ser.write(f"$H{axis}\n".encode())

    # for axis in ["X", "Z", "Y"]:
    #     print(f">>> Homing {axis}")
    #     ser.write(f"$H{axis}\n".encode())


def holder_home():

    global ser

    for axis in ["B", "C", "A"]:
        print(f">>> Homing {axis}")
        ser.write(f"$H{axis}\n".encode())
              

def home_x():
    """Home X axis."""

    global ser

    print(">>> Homing X")
    ser.write(b"$HX\n")
    


def home_y():
    """Home Y axis."""

    global ser

    print(">>> Homing Y")
    ser.write(b"$HY\n")
    


def home_z():
    """Home Z axis."""

    global ser

    print(">>> Homing Z")
    ser.write(b"$HZ\n")
    

def publish_gcode(x=0, y=0, z=0, feedrate=1000):

    global ser

    gcode = f"G91 G1 X{x} Y{y} Z{z} F{feedrate}"

    print(f">>> Sending: {gcode}")

    ser.write((gcode + "\n").encode())



def publish_absolute(x=None, y=None, z=None, feedrate=1000):

    global ser

    axis_commands = []

    if x is not None:
        axis_commands.append(f"X{x}")

    if y is not None:
        axis_commands.append(f"Y{y}")

    if z is not None:
        axis_commands.append(f"Z{z}")

    gcode = f"G90 G1 {' '.join(axis_commands)} F{feedrate}"

    print(f">>> Sending: {gcode}")

    ser.write((gcode + "\n").encode())



def publish_gcode_hal2(x=0, feedrate=1000):

    global ser2

    gcode = f"G91 G1 X{x} F{feedrate}"

    print(f">>> Sending to HAL2: {gcode}")

    ser2.write((gcode + "\n").encode())



#get value

def get_current_x_position():

    global ser

    ser.write(b"?")

    time.sleep(0.05)

    while True:

        response = ser.readline().decode(errors="ignore").strip()

        if "MPos:" in response:

            position_part = response.split("MPos:")[1].split("|")[0]

            x = float(position_part.split(",")[0])

            return x


def get_current_y_position():

    global ser

    ser.write(b"?")

    time.sleep(0.05)

    while True:

        response = ser.readline().decode(errors="ignore").strip()

        if "MPos:" in response:

            position_part = response.split("MPos:")[1].split("|")[0]

            y = float(position_part.split(",")[1])

            return y


def get_current_z_position():

    global ser

    ser.write(b"?")

    time.sleep(0.05)

    while True:

        response = ser.readline().decode(errors="ignore").strip()

        if "MPos:" in response:

            position_part = response.split("MPos:")[1].split("|")[0]

            z = float(position_part.split(",")[2])

            return z




def wait_until_high(pin):

    global ser

    print(f">>> Waiting for digital input GPIO {pin} to become HIGH...")

    while True:

        ser.write(b"?")

        time.sleep(0.05)

        while ser.in_waiting:

            response = ser.readline().decode(
                errors="ignore"
            ).strip()

            if "Pn:" in response:

                pin_part = response.split("Pn:")[1].split("|")[0]

                # GPIO input is HIGH / active
                if str(pin) in pin_part:

                    print(f">>> GPIO {pin} is HIGH")
                    print(">>> Stopping jog...")

                    block_jog()

                    return

        time.sleep(0.05)


        
# search_connect()
# reset()
# time.sleep(1)
# reset2()
# time.sleep(1)
# unlock()
# time.sleep(1)
# unlock2()
