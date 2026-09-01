import serial
import time

COM_PORT = "COM15"
BAUD_RATE = 115200
SLAVE_ID = 0x01
SCALE_FACTOR = 10000

READ_DISTANCE_COMMAND = bytes([
    0x01,
    0x03,
    0x25,
    0x12,
    0x00,
    0x02,
    0x6F,
    0x02
])

ser = serial.Serial(
    port=COM_PORT,
    baudrate=BAUD_RATE,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=0.5
)


def get_distance():
    ser.reset_input_buffer()

    ser.write(READ_DISTANCE_COMMAND)
    ser.flush()

    response = ser.read(9)

    if len(response) != 9:
        return None

    if response[0] != SLAVE_ID or response[1] != 0x03 or response[2] != 0x04:
        return None

    raw_value = int.from_bytes(response[3:7], byteorder="big")

    return raw_value / SCALE_FACTOR


try:
    while True:
        distance = get_distance()

        if distance is not None:
            print(f"Distance: {distance:.4f} mm")
        else:
            print("No valid distance received")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopped.")

finally:
    ser.close()