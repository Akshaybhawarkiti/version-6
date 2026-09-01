import json
import threading
import time
import math
import hal
import csv
import os

import paho.mqtt.client as mqtt

# ==========================
# MQTT Configuration
# ==========================
BROKER = "localhost"      # Change if your broker is on another machine
PORT = 1883
KEEPALIVE = 60

TOPIC_UI_INPUT = "ui_input"
TOPIC_PLANNER_ALERTS = "planner_alerts"

DATA_FILE = "planner_data.csv"

# ==========================
# Safety Configuration
# ==========================
SAFETY_MARGIN = 2.0  # mm of clearance required before flagging a lip collision

alert_status = 0
alert_type = "NONE"

# Grinding Parameters
reciprocation_distance = None
reciprocation_repetitions = None
vertical_step = None
total_vertical_travel = None
grinding_feedrate = None

# Cylinder Parameters
cylinder_diameter = None
slag_depth = None
hole_diameter = None
disk_thickness = None
cylinder_thickness = None
slag_thickness = None

# Tool Parameters
tool_diameter = None
tool_length = None

# General Feedrate
feedrate = None

# Probe
probed_length = None

# Geometry (computed, shared between approach_calculator and safety_checks)
cylinder_dia = None
cylinder_radius = None
collision_length = None


def set_value(name, value):

    data = {}

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", newline="") as file:
            reader = csv.reader(file)

            for row in reader:
                if len(row) >= 2:
                    data[row[0]] = row[1]

    data[name] = value

    with open(DATA_FILE, "w", newline="") as file:
        writer = csv.writer(file)

        for key, val in data.items():
            writer.writerow([key, val])



def get_value(name):

    if not os.path.exists(DATA_FILE):
        return None

    with open(DATA_FILE, "r", newline="") as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) >= 2 and row[0] == name:
                return float(row[1])

    return None

# ==========================
# MQTT Callbacks
# ==========================
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to MQTT Broker.")
        client.subscribe(TOPIC_UI_INPUT)
        print(f"Subscribed to: {TOPIC_UI_INPUT}")

        # Wipe any stale retained alert left over from a previous session
        # (an empty retained payload tells the broker to delete it)
        client.publish(TOPIC_PLANNER_ALERTS, payload=None, retain=True)
        print("Cleared any stale retained alert on planner_alerts")
    else:
        print(f"Connection failed. Return code: {rc}")


def on_message(client, userdata, msg):
    global reciprocation_distance
    global reciprocation_repetitions
    global vertical_step
    global total_vertical_travel
    global grinding_feedrate

    global cylinder_diameter
    global slag_depth
    global hole_diameter
    global disk_thickness
    global cylinder_thickness
    global slag_thickness

    global tool_diameter
    global tool_length

    global feedrate

    global probed_length

    payload = msg.payload.decode()

    print("\nReceived on ui_input:")
    print(payload)
    

    try:
        data = json.loads(payload)

        # Grinding Parameters
        reciprocation_distance = data["reciprocation_distance"]
        reciprocation_repetitions = data["reciprocation_repetitions"]
        vertical_step = data["vertical_step"]
        total_vertical_travel = data["total_vertical_travel"]
        grinding_feedrate = data["grinding_feedrate"]

        # Cylinder Parameters
        cylinder_diameter = data["cylinder_diameter"]
        slag_depth = data["slag_depth"]
        hole_diameter = data["hole_diameter"]
        disk_thickness = data["disk_thickness"]
        cylinder_thickness = data["cylinder_thickness"]
        slag_thickness = data["slag_thickness"]

        # Tool Parameters
        tool_diameter = data["tool_diameter"]
        tool_length = data["tool_length"]

        # Probe
        probed_length = data["probed_length"]


        # General Feedrate
        feedrate = data["feedrate"]

        print("\nCylinder data stored successfully.")

        print("\n========== RECEIVED CYLINDER PARAMETERS ==========")

        print("\nGrinding Parameters")
        print(f"  Reciprocation Distance     : {reciprocation_distance}")
        print(f"  Reciprocation Repetitions  : {reciprocation_repetitions}")
        print(f"  Vertical Step              : {vertical_step}")
        print(f"  Total Vertical Travel      : {total_vertical_travel}")
        print(f"  Grinding Feedrate          : {grinding_feedrate}")

        print("\nCylinder Parameters")
        print(f"  Cylinder Diameter          : {cylinder_diameter}")
        print(f"  Slag Depth                 : {slag_depth}")
        print(f"  Hole Diameter              : {hole_diameter}")
        print(f"  Disk Thickness             : {disk_thickness}")
        print(f"  Cylinder Thickness         : {cylinder_thickness}")
        print(f"  Slag Thickness             : {slag_thickness}")

        print("\nTool Parameters")
        print(f"  Tool Diameter              : {tool_diameter}")
        print(f"  Tool Length                : {tool_length}")

        print("\nProbe Parameters")
        print(f"  Probed Length              : {probed_length}")

        print("\nGeneral Parameters")
        print(f"  Feedrate                   : {feedrate}")

        print("==================================================\n")

        client.publish(TOPIC_PLANNER_ALERTS, "Received cylinder")

        hal.clear_position_file()
        approach_calculator()
        safety_checks()


    except json.JSONDecodeError:
        print("Received command:", payload)

        if payload == "stop":
            hal.feed_hold()
            client.publish(TOPIC_PLANNER_ALERTS, "Feed Hold Sent")

        elif payload == "execute_next":
            hal.reset()
            hal.unlock()
            client.publish(TOPIC_PLANNER_ALERTS, "Reset Sent")

        elif payload == "home":

            client.publish(TOPIC_PLANNER_ALERTS, "Homing all")

            hal.home_all()
            
            client.publish(TOPIC_PLANNER_ALERTS, "Homing DONE")

            ###################################################3

        elif payload == "P0_ON":
            hal.TurnON(0)
            client.publish(TOPIC_PLANNER_ALERTS, "P0_ON")

        elif payload == "P0_OFF":
            hal.TurnOFF(0)
            client.publish(TOPIC_PLANNER_ALERTS, "P0_ON")

        elif payload == "P1_ON":
            hal.TurnON(1)
            client.publish(TOPIC_PLANNER_ALERTS, "P1_ON")
        
        elif payload == "P1_OFF":
            hal.TurnOFF(1)
            client.publish(TOPIC_PLANNER_ALERTS, "P1_ON")

        elif payload == "P2_ON":
            hal.Plus_hal2("X") # rotate the chuck 360 degrees
            client.publish(TOPIC_PLANNER_ALERTS, "Chuck Rotation Jog")
                
        elif payload == "P2_OFF":
            hal.block_jog_hal2()
            client.publish(TOPIC_PLANNER_ALERTS, "Chuck Rotation Jog Block")

            #####################################################3

        elif payload == "block":
            hal.block_jog()
            client.publish(TOPIC_PLANNER_ALERTS, "block")

            #####################################################3

        elif payload == "A+":
            hal.Plus("A")
            client.publish(TOPIC_PLANNER_ALERTS, "A+")

        elif payload == "A-":
            hal.Mins("A")
            client.publish(TOPIC_PLANNER_ALERTS, "A-")


        elif payload == "B+":
            hal.Plus("B")
            client.publish(TOPIC_PLANNER_ALERTS, "B+")
        
        elif payload == "B-":
            hal.Mins("B")
            client.publish(TOPIC_PLANNER_ALERTS, "B-")


        elif payload == "C+":
            hal.Plus("C")
            client.publish(TOPIC_PLANNER_ALERTS, "C+")
                
        elif payload == "C-":
            hal.Mins("C")
            client.publish(TOPIC_PLANNER_ALERTS, "C-")


        ###########################################################################3

        elif payload == "X+":
            hal.Plus("X")
            client.publish(TOPIC_PLANNER_ALERTS, "X+")

        elif payload == "X-":
            hal.Mins("X")
            client.publish(TOPIC_PLANNER_ALERTS, "X-")


        elif payload == "Y+":
            hal.Plus("Y")
            client.publish(TOPIC_PLANNER_ALERTS, "Y+")
        
        elif payload == "Y-":
            hal.Mins("Y")
            client.publish(TOPIC_PLANNER_ALERTS, "Y-")


        elif payload == "Z+":
            hal.Plus("Z")
            client.publish(TOPIC_PLANNER_ALERTS, "Z+")
                
        elif payload == "Z-":
            hal.Mins("Z")
            client.publish(TOPIC_PLANNER_ALERTS, "Z-")


        #############################################################################

        elif payload == "holder_home":

            client.publish(TOPIC_PLANNER_ALERTS, "Homing Holders")

            hal.holder_home()

            client.publish(TOPIC_PLANNER_ALERTS, "Homing DONE")

            

        elif payload == "recover":

            upmaxing = get_value("upmax")
            x_retraction = get_value("x_retract")

            client.publish(TOPIC_PLANNER_ALERTS, f"Recovering ALL from {upmaxing} and {x_retraction}")

            hal.recover_position(upmaxing, x_retraction)

            client.publish(TOPIC_PLANNER_ALERTS, "Recovering DONE now at 0  0  0")
            
            hal.clear_position_file()

            client.publish(TOPIC_PLANNER_ALERTS, "Recovery file Cleared")

def safety_checks():
    global alert_status
    global alert_type
    global collision_length

    try:
        # ==========================================================
        # REQUIRED VALUE CHECK
        # ==========================================================
        required_values = {
            "Cylinder Diameter": cylinder_diameter,
            "Slag Depth": slag_depth,
            "Hole Diameter": hole_diameter,
            "Tool Diameter": tool_diameter,
            "Tool Length": tool_length,
            "Probed Length": probed_length,
            "Disk Thickness": disk_thickness,
        }

        for name, value in required_values.items():
            if value is None:
                alert_status = 1
                alert_type = f"Missing {name}"

                print(f"\nSAFETY CHECK ABORTED - Missing {name}")

                client.publish(TOPIC_PLANNER_ALERTS, f"Missing {name}")

                return

        # ==========================================================
        # LIP COLLISION CHECK
        # (tool must physically fit through the hole)
        # ==========================================================
        effective_hole_dia = hole_diameter - tool_diameter

        if effective_hole_dia <= 0:
            alert_status = 1
            alert_type = "Collision to Lip"

            print("\n========== SAFETY CHECK ==========")
            print("ERROR : Tool diameter is larger than hole diameter.")
            print("STATUS: NOT SAFE")
            print("==================================\n")

            client.publish(TOPIC_PLANNER_ALERTS, "Collision to Lip")
            return

        effective_hole_radius = effective_hole_dia / 2.0

        # ==========================================================
        # SAFE APPROACH ANGLE WINDOW
        # (the angle must stay within the range that keeps the tool
        #  clear of both edges of the hole)
        # ==========================================================
        min_side = cylinder_radius - effective_hole_radius
        max_side = cylinder_radius + effective_hole_radius

        min_comp_angle = math.degrees(
            math.atan(min_side / slag_depth)
        )
        max_comp_angle = math.degrees(
            math.atan(max_side / slag_depth)
        )

        max_allowed_approach_angle = 90.0 - min_comp_angle
        min_allowed_approach_angle = 90.0 - max_comp_angle

        angle_safe = (
            min_allowed_approach_angle <= approach_angle <= max_allowed_approach_angle
        )

        # ==========================================================
        # DISK COLLISION CHECK
        # ==========================================================
        collision_length = (
            effective_hole_radius /
            math.tan(math.radians(comp_angle))
        )

        disk_collision_safe = (
            collision_length >= disk_thickness
        )

        errors = []
        if not angle_safe:
            errors.append("Invalid Approach Angle")
        if not disk_collision_safe:
            errors.append("Disk Collision Risk")

        # ==========================================================
        # FINAL RESULT
        # ==========================================================
        print("\n========== SAFETY CHECK ==========")
        print(f"Safe Approach Angle Window : {min_allowed_approach_angle:.4f} to {max_allowed_approach_angle:.4f}")
        print(f"Approach Angle             : {approach_angle:.4f}  -> {'SAFE' if angle_safe else 'UNSAFE'}")
        print(f"Collision Length           : {collision_length:.4f}  -> {'SAFE' if disk_collision_safe else 'UNSAFE'}")

        if len(errors) == 0:
            alert_status = 0
            alert_type = "NONE"

            print("GOOD TO GO")
            print("Alert Status : 0")
            print("==================================\n")

            client.publish(TOPIC_PLANNER_ALERTS, "GOOD TO GO")

            # Run the hardware sequence on its own thread. sequence() blocks
            # on hal.wait_until_idle(), and on_message runs on the same
            # thread as client.loop_forever() — calling sequence() directly
            # here would stall the MQTT network loop for the whole sequence,
            # preventing any further publish/subscribe traffic from being
            # processed until it finishes.
            threading.Thread(target=sequence, daemon=True).start()

        else:
            alert_status = 1
            alert_type = errors[0]

            print("DANGER APPROACH")
            print("Alert Status : 1")
            print("Reason(s):")
            for error in errors:
                print(f" - {error}")
            print("==================================\n")

            client.publish(TOPIC_PLANNER_ALERTS, "DANGER APPROACH: " + ", ".join(errors))

    except Exception as e:
        # Any failure in the safety check itself must fail SAFE, not silently
        # keep the previous alert_status/alert_type.
        alert_status = 1
        alert_type = "CALC ERROR"

        print("\n========== SAFETY CHECK ERROR ==========")
        print(f"Exception during safety check: {e}")
        print("Alert Status : 1 (forced unsafe)")
        print("=========================================\n")

        client.publish(TOPIC_PLANNER_ALERTS, "CALC ERROR")


def approach_calculator():
    global approach_angle
    global comp_angle

    global raw_z_below

    global tool_offsetx
    global tool_offsetz

    global targetx
    global targetz

    global akshay_a
    global akshay_b

    global cylinder_dia
    global cylinder_radius

    global cylinder_diameter
    global cylinder_thickness
    global slag_thickness
    global slag_depth
    global tool_length
    global probed_length

    client.publish(TOPIC_PLANNER_ALERTS, "Started the Calculation for Cylinder")
    client.publish(TOPIC_PLANNER_ALERTS, f"Cylinder Diameter {cylinder_dia}")
    client.publish(TOPIC_PLANNER_ALERTS, f"Cylinder Thickness {cylinder_thickness}")
    client.publish(TOPIC_PLANNER_ALERTS, f"Slag Thickness {slag_thickness}")
    client.publish(TOPIC_PLANNER_ALERTS, f"Slag Depth {slag_depth}")
    client.publish(TOPIC_PLANNER_ALERTS, f"Probed Lenght {probed_length}")

    # ==========================================================
    # CALCULATE APPROACH ANGLE
    # ==========================================================

    # offset for slag thickness and cylinder wall thickness
    cylinder_dia = cylinder_diameter - slag_thickness - cylinder_thickness

    # Calculate cylinder radius
    cylinder_radius = cylinder_dia / 2.0

    # Calculate complementary angle
    comp_angle = math.degrees(
        math.atan(cylinder_radius / slag_depth)
    )

    # Calculate approach angle
    approach_angle = 90.0 - comp_angle

    # ==========================================================
    # CALCULATE Z BELOW TRAVEL FROM CYLINDER CENTER
    # ==========================================================

    raw_z_below = (
        probed_length *
        math.tan(math.radians(comp_angle))
    )

    # ==========================================================
    # CALCULATE TOOL OFFSETS
    # ==========================================================

    # Tool X Offset
    tool_offsetx = (
        tool_length *
        math.cos(math.radians(approach_angle))
    )

    # Tool Z Offset
    tool_offsetz = (
        tool_length *
        math.cos(math.radians(comp_angle))
    )

    # ==========================================================
    # CALCULATE FINAL TARGETS
    # ==========================================================

    targetz = (
        raw_z_below +
        cylinder_radius -
        tool_offsetx
    )

    targetx = (
        probed_length +
        slag_depth -
        tool_offsetz
    )

    akshay_a = (
        probed_length +
        slag_depth
    )

    akshay_b = (
        raw_z_below +
        cylinder_radius
    )

    # ==========================================================
    # PRINT RESULTS
    # ==========================================================

    print("\n========== APPROACH CALCULATOR ==========")
    print(f"Approach Angle        : {approach_angle:.4f}")
    print(f"Complement Angle      : {comp_angle:.4f}")
    print(f"Raw Z Below           : {raw_z_below:.4f}")
    print(f"Tool Offset X         : {tool_offsetx:.4f}")
    print(f"Tool Offset Z         : {tool_offsetz:.4f}")
    print(f"Target X              : {targetx:.4f}")
    print(f"Target Z              : {targetz:.4f}")
    print(f"Akshay A              : {akshay_a:.4f}")
    print(f"Akshay B              : {akshay_b:.4f}")
    print("=========================================\n")

    print("=========================================\n")


def sequence():
    print("\n========== SEQUENCE ==========")
    print("Starting grinding sequence...")
    print("================================\n")

    
# ==========================
# Home
# ==========================

    client.publish(TOPIC_PLANNER_ALERTS, "Home to 0 0 0 Position in absoulte")
    hal.publish_absolute(x=0,y=0,z=0,feedrate=feedrate)
    time.sleep(1)
    hal.wait_until_idle()
    
# ==========================
# up the y axis
# ==========================
   
    client.publish(TOPIC_PLANNER_ALERTS, "Moving to Approch position in Y axis")    
    upmax = 372-raw_z_below
    set_value("upmax", upmax)
    hal.publish_gcode(y=upmax,feedrate=feedrate) # take to center constant always
    time.sleep(1)
    hal.wait_until_idle()
    upmaxing = get_value("upmax")
    print(f"Y upmax value retrieved from CSV: {upmaxing}")

# ==================================================================================================
# SENSOR offset to be removed from program onces we get the sensor offset from the machine
# ==================================================================================================
    
    client.publish(TOPIC_PLANNER_ALERTS, "Sensor OFFSet fro 300mm")
    x_retract = 18.0
    set_value("x_retract", x_retract)
    hal.publish_gcode(x=x_retract,feedrate=feedrate) # take to center constant always
    time.sleep(1)
    hal.wait_until_idle()
    x_retraction = get_value("x_retract")
    print(f"X retraction value retrieved from CSV: {x_retraction}")

# ==========================
# angle the tool
# ==========================
    
    client.publish(TOPIC_PLANNER_ALERTS, "Tool Approch Angle")
    hal.publish_gcode(z=approach_angle,feedrate=feedrate) # take to center constant always
    time.sleep(1)
    hal.wait_until_idle()

# ==========================
# Chuck ON
# ==========================

    # hal.TurnON(2) 
    # time.sleep(1)
    # hal.wait_until_idle()
    client.publish(TOPIC_PLANNER_ALERTS, "Rotating Cylinder test")
    hal.publish_gcode_hal2(x=360,feedrate=1440) # rotate the chuck 360 degrees
    
# ==========================
# target x and y IN
# ==========================
    client.publish(TOPIC_PLANNER_ALERTS, "Moving Inside in the angle")
    hal.publish_gcode(x=targetx, y=targetz, feedrate=feedrate) # take to center constant always
    time.sleep(1)
    hal.wait_until_idle()

# ==========================
# Grinder ON
# ==========================
    client.publish(TOPIC_PLANNER_ALERTS, "[Waring] Gringer ON")
    hal.TurnON(0)
    time.sleep(1)
    hal.wait_until_idle()
    
# ==========================
# wait 
# ==========================
    
    client.publish(TOPIC_PLANNER_ALERTS, "Grinding")
    grindingprocess()

# ==========================
# Grinder OFF
# ==========================
    
    client.publish(TOPIC_PLANNER_ALERTS, "[INFO] Grinder Off")
    hal.TurnOFF(0)
    time.sleep(1)
    hal.wait_until_idle()

# ==========================
# Retrive
# ==========================
    
    client.publish(TOPIC_PLANNER_ALERTS, "Retrive the Tool")
    hal.publish_gcode(x=-targetx, y=-targetz, feedrate=feedrate) # take to center constant always
    time.sleep(1)
    hal.wait_until_idle()
    
# ==========================
# reposition
# ==========================
    
    client.publish(TOPIC_PLANNER_ALERTS, "Reset tool")
    hal.publish_gcode(z=-approach_angle,feedrate=feedrate) # take to center constant always
    time.sleep(1)
    hal.wait_until_idle()

# ==========================
# Home
# ==========================
 
    client.publish(TOPIC_PLANNER_ALERTS, "Taking it to HOME")
    hal.publish_absolute(x=0,y=0,z=0,feedrate=feedrate)
    time.sleep(1)
    hal.wait_until_idle()


# ==========================
# Grinding
# ========================== 

def grindingprocess():
    print("\n========== SEQUENCE ==========")
    print("Starting grinding sequence...")
    print("================================\n")

    client.publish(TOPIC_PLANNER_ALERTS, "[Danger] :Starting grinding sequence... [Danger] ")

    print("THE GRINDING PROCESS STARTED")

    number_of_vertical_steps = int(round(total_vertical_travel / vertical_step))

    for i in range(number_of_vertical_steps):

        print(f"\n========== VERTICAL STEP {i + 1}/{number_of_vertical_steps} ==========")
        client.publish(TOPIC_PLANNER_ALERTS, f" [System]  VERTICAL STEP {i + 1}/{number_of_vertical_steps} [System] ")

        # Start from X = 0 relative position
        current_x = 0.0

        # ----------------------------------------------------------
        # GRIND AT EACH X POSITION
        # ----------------------------------------------------------
        while current_x < reciprocation_distance:

            print(f"Grinding at X position: {current_x} mm")
            print("Waiting 60 seconds...")

            client.publish(TOPIC_PLANNER_ALERTS, " [Danger] Cylinder grinding and motion [Danger] ")

            hal.publish_gcode_hal2(x=365,feedrate=1440) # rotate the chuck 360 degrees
 
            time.sleep(15)

            # Calculate next X movement
            remaining_distance = reciprocation_distance - current_x

            if remaining_distance >= 1.0:
                x_step = 1
            else:
                x_step = remaining_distance

            print(f"Moving X +{x_step} mm")

            y_step = 1

            client.publish(TOPIC_PLANNER_ALERTS, f"moving the tool down by {y_step}")
            hal.publish_gcode(y=-y_step,feedrate=feedrate)
            hal.only_idle()

            mess = f"moving {x_step} forward"
            client.publish(TOPIC_PLANNER_ALERTS, mess)
            hal.publish_gcode(x=x_step,feedrate=grinding_feedrate)
            hal.only_idle()

            client.publish(TOPIC_PLANNER_ALERTS, f"[Danger] Moving tool UP by {y_step} [Danger]")
            hal.publish_gcode(y=y_step,feedrate=grinding_feedrate)
            hal.only_idle()

            current_x += x_step

        # ----------------------------------------------------------
        # FINAL 60 SECOND GRIND AT RECIPROCATION DISTANCE
        # ----------------------------------------------------------
        print(f"Grinding at final X position: {current_x} mm")
        print("Waiting 60 seconds...")

        time.sleep(15)

        # ----------------------------------------------------------
        # RETURN X BACK TO START
        # ----------------------------------------------------------
        print(f"Returning X by -{reciprocation_distance} mm")
        client.publish(TOPIC_PLANNER_ALERTS, "Move Back")
        hal.publish_gcode(x=-reciprocation_distance,feedrate=feedrate)
        hal.only_idle()

        # ----------------------------------------------------------
        # MOVE VERTICAL STEP
        # ----------------------------------------------------------
        client.publish(TOPIC_PLANNER_ALERTS, "Move vertical")
        print(f"Moving vertical +{vertical_step} mm")

        hal.publish_gcode(y=vertical_step,feedrate=grinding_feedrate)
        hal.only_idle()

    # --------------------------------------------------------------
    # RETURN VERTICAL AXIS TO ORIGINAL POSITION
    # --------------------------------------------------------------
    print("\n========== GRINDING COMPLETE ==========")

    vertical_step_NEG = total_vertical_travel * -1

    print(f"Moving vertical axis back by {vertical_step_NEG} mm")
    client.publish(TOPIC_PLANNER_ALERTS, f"Moving vertical axis back by {vertical_step_NEG} mm")

    hal.publish_gcode(y=vertical_step_NEG,feedrate=feedrate)
    hal.only_idle()

    print("Grinding sequence completed.")
    client.publish(TOPIC_PLANNER_ALERTS, "[INFO] : Grinding Done : [INFO]")


# ==========================
# Main
# ==========================
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.on_connect = on_connect
client.on_message = on_message

# hal.connect()
# hal.connect2()

client.publish(TOPIC_PLANNER_ALERTS, " [WAIT]  Wait for Connection !!!  [WAIT]")

hal.search_connect()
client.publish(TOPIC_PLANNER_ALERTS, " [WAIT]  Wait for Connection !!!  [WAIT]")

hal.reset()
time.sleep(1)
hal.reset2()
time.sleep(1)
hal.unlock()
time.sleep(1)
hal.unlock2()

client.publish(TOPIC_PLANNER_ALERTS, " [DONE]  Connection Done [DONE]")

client.connect(BROKER, PORT, KEEPALIVE)

client.loop_forever()