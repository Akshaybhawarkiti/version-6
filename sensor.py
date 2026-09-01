import serial

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

    try:

        ser.reset_input_buffer()

        ser.write(READ_DISTANCE_COMMAND)
        ser.flush()

        response = ser.read(9)

        if len(response) != 9:
            return None

        if response[0] != SLAVE_ID:
            return None

        if response[1] != 0x03:
            return None

        if response[2] != 0x04:
            return None

        raw_value = int.from_bytes(
            response[3:7],
            byteorder="big"
        )

        return raw_value / SCALE_FACTOR

    except serial.SerialTimeoutException:

        return None

    except serial.SerialException:

        return None

    except Exception:

        return None

# value = get_distance()
# print (value)