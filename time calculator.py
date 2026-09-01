import math


def calculate_grinding_time():
    reciprocation_distance = float(input("Reciprocation distance (mm): "))
    total_vertical_travel = float(input("Total vertical travel (mm): "))
    slag_depth = float(input("Slag depth (mm): "))
    vertical_step = float(input("Vertical step (mm): "))
    grinding_feedrate = float(input("Grinding feedrate (mm/s): ")) / 60

    # ==========================================================
    # GRINDING SETTINGS FROM MAIN LOGIC
    # ==========================================================

    # X movement happens in 0.5 mm increments
    x_step = 0.5

    # Waiting time at every X position
    wait_per_x_position = 15

    # Final wait at the end of every vertical layer
    final_wait = 15

    # ==========================================================
    # NUMBER OF VERTICAL STEPS
    # ==========================================================

    number_of_vertical_steps = int(
        round(total_vertical_travel / vertical_step)
    )

    # ==========================================================
    # NUMBER OF X POSITIONS PER VERTICAL STEP
    # ==========================================================

    number_of_x_positions = int(
        math.ceil(reciprocation_distance / x_step)
    )

    # ==========================================================
    # TIME CALCULATION FOR ONE VERTICAL STEP
    # ==========================================================

    # Waiting at every X position
    wait_time = number_of_x_positions * wait_per_x_position

    # Forward X movement
    forward_x_time = reciprocation_distance / grinding_feedrate

    # Z +1 and Z -1 movement at every X position
    z_movement_time = (
        number_of_x_positions * 2 / grinding_feedrate
    )

    # X return to starting position
    return_x_time = reciprocation_distance / grinding_feedrate

    # Vertical movement to next layer
    vertical_move_time = vertical_step / grinding_feedrate

    # Final wait at end of layer
    final_wait_time = final_wait

    # Total time for one vertical layer
    time_per_vertical_step = (
        wait_time
        + forward_x_time
        + z_movement_time
        + return_x_time
        + vertical_move_time
        + final_wait_time
    )

    # ==========================================================
    # TOTAL GRINDING TIME
    # ==========================================================

    total_grinding_time = (
        time_per_vertical_step * number_of_vertical_steps
    )

    # ==========================================================
    # FINAL VERTICAL RETURN
    # ==========================================================

    final_vertical_return_time = (
        total_vertical_travel / grinding_feedrate
    )

    total_grinding_time += final_vertical_return_time

    # ==========================================================
    # TIME CONVERSION
    # ==========================================================

    total_seconds = total_grinding_time

    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60

    # ==========================================================
    # PRINT RESULTS
    # ==========================================================

    print("\n==========================================")
    print("         GRINDING TIME CALCULATOR")
    print("==========================================")

    print("\nINPUT SETTINGS")
    print("------------------------------------------")
    print(f"Reciprocation distance : {reciprocation_distance:.2f} mm")
    print(f"Total vertical travel  : {total_vertical_travel:.2f} mm")
    print(f"Slag depth             : {slag_depth:.2f} mm")
    print(f"Vertical step          : {vertical_step:.2f} mm")
    print(f"Grinding feedrate      : {grinding_feedrate:.2f} mm/s")

    print("\nCALCULATED STEPS")
    print("------------------------------------------")
    print(f"Number of vertical steps : {number_of_vertical_steps}")
    print(f"X positions per step     : {number_of_x_positions}")

    print("\nTIME CALCULATION")
    print("------------------------------------------")
    print(f"Time per vertical step : {time_per_vertical_step:.2f} seconds")
    print(f"Total grinding time    : {total_seconds:.2f} seconds")

    print("\nTOTAL TIME")
    print("------------------------------------------")
    print(f"{hours} hours {minutes} minutes {seconds:.2f} seconds")
    print(f"Total minutes : {total_seconds / 60:.2f}")
    print(f"Total hours   : {total_seconds / 3600:.2f}")

    print("==========================================\n")


calculate_grinding_time()