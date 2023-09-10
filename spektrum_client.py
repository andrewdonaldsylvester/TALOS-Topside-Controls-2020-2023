from serial import Serial
import socket
import pickle
import glob
import time
# Look up serial port for arduino
# Connect to Pi first, then run app


def invert_channel(value):
    return 3000 - value


def shrink_channel(value, scale):
    return 1500 + (value - 1500) / scale


def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def clamp(x, in_min, in_max):
    return max(in_min, min(x, in_max))


def clamp_if_near(x, clamp_value, epsilon, return_value=1500):
    if abs(x - clamp_value) <= epsilon:
        return return_value
    else:
        return x


ip = "192.168.1.2" # ROV IP!!!

serverAddressPort = (ip, 20001)

bufferSize = 128

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

send_message = pickle.dumps([1500, 1500, 1500, 1500,
                                 1500, 1500, 1500, 1500,
                                 1500, 1500, 1500, 1500,
                                 1500, 1500, 1500, 1500])

try:
    UDPClientSocket.sendto(send_message, serverAddressPort)
except:
    print("Connection Lost, reconnecting...")
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    # print("Reconnected!")

arduino_port = glob.glob('/dev/cu.usbmodem*')[0]
ser = Serial(arduino_port, 115200)

# flashlight_state = False
# pump_state = False

try:
    if ser.is_open:

        send_message = pickle.dumps([1500, 1500, 1500, 1500,
                                     1500, 1500, 0, 0,
                                     0, 0, 0, 0,
                                     0, 0, 0, 0])

        UDPClientSocket.sendto(send_message, serverAddressPort)

        R_SW_STATE = 0
        L_SW_STATE = 0

        FLASHLIGHT_SIG = 0
        SERVO_SIG = 1000
        PUMP_SIG = 0
        VALVE_SIG = 0



        while True:
            values = ser.readline()
            channels = values.split()

            print(channels)

            if len(channels) < 6:
                continue

            L_X = invert_channel(int(channels[2])) - 7
            L_Y = int(channels[5]) - 25
            R_X = int(channels[4])
            R_Y = int(channels[3])

            # L_X = clamp_if_near(L_X, 1500m5, return_value=1500)
            # R_Y = 1425

            LEFT_SWITCH = int(channels[1])

            if 800 <= LEFT_SWITCH <= 1500:
                L_SW_STATE = 1
            elif 1501 <= LEFT_SWITCH <= 2200:
                L_SW_STATE = 0

            # if 800 <= LEFT_SWITCH <= 1500:
            #     SWITCH_SIG = 1000
            # elif 1501 <= LEFT_SWITCH <= 2200:
            #     SWITCH_SIG = 2250

            # if 800 <= LEFT_SWITCH <= 1200:
            #     FLASHLIGHT_SIG = 15000
            #
            #     SERVO_SIG = 1000
            # elif 1300 <= LEFT_SWITCH <= 1700:
            #     FLASHLIGHT_SIG = 0
            #
            #     SERVO_SIG = 2250
            # elif 1800 <= LEFT_SWITCH <= 2200:
            #     FLASHLIGHT_SIG = 0
            #
            #     SERVO_SIG = 1000


            RIGHT_SWITCH = int(channels[0])

            if 800 <= RIGHT_SWITCH <= 1200:
                R_SW_STATE = 2
            elif 1300 <= RIGHT_SWITCH <= 1700:
                R_SW_STATE = 1
            elif 1800 <= RIGHT_SWITCH <= 2200:
                R_SW_STATE = 0


            # if 800 <= RIGHT_SWITCH <= 1200:
            #     FLASHLIGHT_SIG = 0
            #     PUMP_SIG = 18777
            # elif 1300 <= RIGHT_SWITCH <= 1700:
            #     FLASHLIGHT_SIG = 0
            #     PUMP_SIG = 0
            # elif 1800 <= RIGHT_SWITCH <= 2200:
            #     FLASHLIGHT_SIG = 15000
            #     PUMP_SIG = 0

            # if 800 <= RIGHT_SWITCH <= 1200:
            #     PUMP_SIG = 18777  # both
            #     VALVE_SIG = 18777
            # elif 1300 <= RIGHT_SWITCH <= 1700:
            #     PUMP_SIG = 0  # neither
            #     VALVE_SIG = 0
            # elif 1800 <= RIGHT_SWITCH <= 2200:
            #     PUMP_SIG = 18777  # just pump
            #     VALVE_SIG = 0

            print(L_SW_STATE, R_SW_STATE)

            if L_SW_STATE == 0:
                if R_SW_STATE == 0:
                    SERVO_SIG = 1000
                    FLASHLIGHT_SIG = 0
                    PUMP_SIG = 18777
                    VALVE_SIG = 0
                elif R_SW_STATE == 1:
                    SERVO_SIG = 1000
                    FLASHLIGHT_SIG = 0
                    PUMP_SIG = 18777
                    VALVE_SIG = 18777
                elif R_SW_STATE == 2:
                    SERVO_SIG = 2250
                    FLASHLIGHT_SIG = 0
                    PUMP_SIG = 0
                    VALVE_SIG = 18777
            elif L_SW_STATE == 1:
                if R_SW_STATE == 0:
                    SERVO_SIG = 1000
                    FLASHLIGHT_SIG = 0
                    PUMP_SIG = 0
                    VALVE_SIG = 0
                elif R_SW_STATE == 1:
                    SERVO_SIG = 2250
                    FLASHLIGHT_SIG = 0
                    PUMP_SIG = 0
                    VALVE_SIG = 0
                elif R_SW_STATE == 2:
                    SERVO_SIG = 2250
                    FLASHLIGHT_SIG = 15000
                    PUMP_SIG = 0
                    VALVE_SIG = 0



            # print("L_X {} L_Y {} R_X {} R_Y {} BINARY_SWITCH {} TERNARY_SWITCH {}"
            #       .format(L_X, L_Y, R_X, R_Y, BINARY_SWITCH, TERNARY_SWITCH))

            # forward = R_Y
            # strafe = R_X
            # turn = L_X
            # altitude = L_Y

            forward = R_Y
            strafe = L_X
            turn = R_X
            altitude = L_Y

            # speed_modifier = {"LO": 3, "MID": 2, "HI": 1}

            # M1 = forward - strafe - shrink_channel(turn, 2) + 3000
            # M2 = forward + strafe + shrink_channel(turn, 2) - 3000
            # M3 = forward + strafe - shrink_channel(turn, 2)
            # M4 = forward - strafe + shrink_channel(turn, 2)

            # Updated
            M1 = (forward) - strafe - shrink_channel(turn, 2) + 3000
            M2 = -(forward) + strafe - shrink_channel(turn, 2) + 3000
            M3 = -(forward) - strafe + shrink_channel(turn, 2) + 3000
            M4 = (forward) + strafe + shrink_channel(turn, 2) - 3000

            # M1 = forward + strafe + shrink_channel(turn, 2) - 3000
            # M2 = forward - strafe - shrink_channel(turn, 2) + 3000
            # M3 = -forward + strafe - shrink_channel(turn, 2) + 3000
            # M4 = -forward - strafe + shrink_channel(turn, 2) + 3000

            # Motor      1 2 3 4
            # Forward    + + - -
            # Right      + - + -
            # Clockwise  + - - +

            # if abs(altitude - 1500) <= 100:
            #     altitude = 1500


            M5 = altitude
            M6 = altitude

            M1 = clamp(M1, 1100, 1900)
            M2 = clamp(M2, 1100, 1900)
            M3 = clamp(M3, 1100, 1900)
            M4 = clamp(M4, 1100, 1900)
            M5 = clamp(M5, 1100, 1900)
            M6 = clamp(M6, 1100, 1900)

            # Reverse Motors
            M1 = map_value(M1, 1100, 1900, 1900, 1100)
            M2 = map_value(M2, 1100, 1900, 1900, 1100)
            # M3 = map_value(M3, 1100, 1900, 1100, 1900)
            # M4 = map_value(M4, 1100, 1900, 1900, 1100)
            # M5 = map_value(M5, 1100, 1900, 1100, 1900)
            # M6 = map_value(M6, 1100, 1900, 1100, 1900)

            M1 = map_value(M1, 1100, 1900, 1250, 1750)
            M2 = map_value(M2, 1100, 1900, 1250, 1750)
            M3 = map_value(M3, 1100, 1900, 1250, 1750)
            M4 = map_value(M4, 1100, 1900, 1250, 1750)
            M5 = map_value(M5, 1100, 1900, 1250, 1750)
            M6 = map_value(M6, 1100, 1900, 1250, 1750)

            M1 = round(clamp(M1, 1250, 1750))
            M2 = round(clamp(M2, 1250, 1750))
            M3 = round(clamp(M3, 1250, 1750))
            M4 = round(clamp(M4, 1250, 1750))
            M5 = round(clamp(M5, 1250, 1750))
            M6 = round(clamp(M6, 1250, 1750))

            e = 20

            M1 = clamp_if_near(M1, 1500, e, return_value=1484)
            M2 = clamp_if_near(M2, 1500, e, return_value=1484)
            M3 = clamp_if_near(M3, 1500, e, return_value=1484)
            M4 = clamp_if_near(M4, 1500, e, return_value=1484)
            M5 = clamp_if_near(M5, 1500, e, return_value=1484)
            M6 = clamp_if_near(M6, 1500, e, return_value=1484)

            """ ADD CODE TO USE FLASHLIGHT AND PUMP STATES TO TOGGLE SWITCHES WITH THEIR CHANNELS """
            """ PINS S6 LEFT UV FLASHLIGHT AND S7 RIGHT PUMP """
            """ GRIPPER ON S9 """


            # The strange order is there to rectify the wiring layout
            send_message = pickle.dumps([M4, M3, M6, M5,
                                         M2, M1, FLASHLIGHT_SIG, PUMP_SIG,
                                         VALVE_SIG, SERVO_SIG, 0, 0,
                                         0, 0, 0, 0])

            # send_message = pickle.dumps([1500, 1500, 1500, 1500,
            #                              1500, 1500, 0, 0,
            #                              0, 0, 0, 0,
            #                              0, 0, 0, 0])

            # send_message = pickle.dumps([0, 0, 0, 0,
            #                              0, 0, 0, 0,
            #                              0, 0, 0, 0,
            #                              0, 0, 0, 0])

            try:
                UDPClientSocket.sendto(send_message, serverAddressPort)
            except:
                print("Connection Lost, reconnecting...")
                UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
                # print("Reconnected!")

            print("M1 = {:5} \t M2 = {:5} \t M3 = {:5} \t M4 = {:5} \t M5 = {:5} \t M6 = {:5} \t S1 = {:5} \t Flashlight = {:5} \t Pump = {:5}"
                  .format(round(M1), round(M2), M3, M4, M5, M6, SERVO_SIG, FLASHLIGHT_SIG, PUMP_SIG))
finally:

    send_message = pickle.dumps([0, 0, 0, 0,
                                 0, 0, 0, 0,
                                 0, 0, 0, 0,
                                 0, 0, 0, 0])
    UDPClientSocket.sendto(send_message, serverAddressPort)


    print("Closing Connection")

    ser.close()
