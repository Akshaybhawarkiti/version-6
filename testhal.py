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


current_x = hal.get_current_x_position()
current_y = hal.get_current_y_position()
current_z = hal.get_current_z_position()

print(current_x)
print(current_y)
print(current_z)



hal.publish_gcode(x=20,y=30,z=1,feedrate=1000)
time.sleep(1)
hal.wait_until_idle()

current_x = hal.get_current_x_position()
current_y = hal.get_current_y_position()
current_z = hal.get_current_z_position()

print(current_x)
print(current_y)
print(current_z)


hal.publish_gcode(x=-20,y=-30,z=-1,feedrate=1000)
time.sleep(1)
hal.wait_until_idle()

current_x = hal.get_current_x_position()
current_y = hal.get_current_y_position()
current_z = hal.get_current_z_position()

print(current_x)
print(current_y)
print(current_z)
