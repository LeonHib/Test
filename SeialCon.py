#!/usr/bin/env python3
"""
ISD communication and activation vua UART RS-422 asynchronous interface

Written by Leon Hibnik
IMI Systems ltd. property
"""

import serial
import serial.tools.list_ports
from tkinter import *
from time import time, sleep
import serial.rs485

# ser = serial.Serial('COM4', 9600, timeout=0)
# ser2 = serial.Serial("COM7", 9600, timeout=0, )  # TESTING!!!
# ser2 = serial.Serial("COM7", 9600, timeout=0,)
# ser2.rs485_mode = serial.rs485.RS485Settings()
# ser2.setDTR(1)
# ser2.setRTS(1)
# print(ser2)


# globals
ESAD_LOGIC_STATES = {
    0: "Before Act Voltage",
    1: "Fire module operating",
    2: "Fire module complete BIT",
    3: "ESAD Wait for Arm Enable",
    4: "Arm Enable OK",
    5: "Arm Command received",
    6: "Fire Cap charging...",
    7: "ESAD Ready to FIRE",
    8: "Fire Command received",
    9: "ESAD Fired",
    51: "ESAD Test mode",
    129: "DUD, RAM check",
    130: "DUD, Flash check",
    131: "DUD, Active ARM_EN input on start",
    132: "DUD, Active ARM_EN decode on start",
    133: "DUD, Active Fire Signal input on start",
    134: "DUD, Active Fire Signal decode on start",
    135: "DUD, No 15V after first switch on start",
    136: "DUD, 15V present after second switch on start",
    139: "DUD, Software trap",
    141: "DUD, analog measurement fail",
    161: "DUD, ARM Enable HW/SW Issue",
    162: "DUD, Fire Signal HW/SW Issue",
    167: "DUD, Fire Cap not charging",
    168: "DUD, Fire Cap no discharging",
    169: "DUD, Fire Cap discharge switch fail",
    175: "DUD, Fire Func not in order",
    176: "DUD, Fire func not in CPU logic",
    180: "DUD, Communication unit PBIT fail",
    181: "DUD, Wrong Weapon system, ID message",
    182: "DUD, Wrong ESAD type, ID Message",
    185: "DUD, RAM check",
    190: "DUD, SW trap fail, Test mode"
}

BAUDRATES = (50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800, 2400, 4800,
             9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600)
running = 0
ser = None
in_msg = []
# in_msg = [0x75, 0x39, 0x53, 0x99, 0x65, 0x78, 0xb5]  # TESTING ONLY!!!!


class esad_gui:
    """Class object for GUI, create the main frames and buttons"""
    def __init__(self, master):
        self.master = master
        master.geometry("500x400")
        master.title("ESAD ISD GUI")
        self.ports = list(serial.tools.list_ports.comports())
        self.ports_list = []
        self.port_chosen = StringVar()
        self.port_chosen.set("")
        for port in self.ports:
            self.ports_list.append(str(port)[:4])
        self.baud_chosen = StringVar()
        self.baud_chosen.set("9600")

        # *** Buttons ***
        self.frame_buttons = Frame(master, bg="grey", width="250", height="400")
        self.frame_buttons.pack(side=LEFT, fill=Y)
        self.frame_text = Frame(master, bg="black", width="250")
        self.frame_text.pack(side=TOP, anchor=E, fill=BOTH, expand=1)

        self.button_open_uart = Button(self.frame_buttons, width="20",
                                       text="Open UART", command=self.uart_conf)
        self.button_open_uart.pack(side=TOP, padx="20", pady="20")
        self.button_init = Button(self.frame_buttons, width="20",
                                  text="Send ISD ID", fg="green", command=send_ESAD_ISD_ID_COMMAND)
        self.button_init.pack(pady="10", side=TOP)
        self.button_status = Button(self.frame_buttons, width="20",
                                    text="Send Status Req", fg="black", command=status_req_task)
        self.button_status.pack(pady="10", side=TOP)
        self.button_ARM = Button(self.frame_buttons, width="20",
                                 text="Send ARM Command", fg="red", command=send_ESAD_SA_COMMAND)
        self.button_ARM.pack(pady="10", side=TOP)

        # self.comm_port = Entry(self.frame_buttons)
        # self.comm_port.insert(0, "COM port")
        # self.comm_port.pack()
        # self.baud_input = Entry(self.frame_buttons)
        # self.baud_input.insert(0, "BUAD rate")
        # self.baud_input.pack()
        self.ports_label = Label(self.frame_buttons, text="Select Port", bg="grey")
        self.ports_label.pack()
        self.ports_menu = OptionMenu(self.frame_buttons, self.port_chosen, *self.ports_list)
        self.ports_menu.pack()
        self.baud_label = Label(self.frame_buttons, text="Select Baud Rate", bg="grey")
        self.baud_label.pack()
        self.baud_menu = OptionMenu(self.frame_buttons, self.baud_chosen, *BAUDRATES)
        self.baud_menu.pack()

        # *** Text lines ***
        self.lines = []
        for line in range(8):
            var = StringVar()
            self.lines.append(var)
            self.lines[line].set("")
        self.lines[0].set("ISD Operation Screen")
        self.labels_display = []
        for line in range(8):
            if line == 0:
                var = Label(self.frame_text, textvariable=self.lines[line], bg="black", fg="white", font=(None, 15))
            else:
                var = Label(self.frame_text, textvariable=self.lines[line], bg="black", fg="white")
            self.labels_display.append(var)
            self.labels_display[line].pack()
        button_clear = Button(self.frame_buttons, text="Clear Screen", command=self.clear)
        button_clear.pack(pady=10)
        button_close = Button(self.frame_buttons, text="Stop, Close", command=self.end)
        button_close.pack()

    def uart_conf(self):
        for line in self.lines:
            line.set("")
        self.lines[0].set("ISD Operation Screen")
        # try:
        #     open_uart_port(self.comm_port.get(), self.baud_input.get())
        # except ValueError:
        #     self.lines[1].set("Error opening serial port: {}".format(ValueError))
        # open_uart_port(self.comm_port.get(), self.baud_input.get())
        open_uart_port(self.port_chosen.get(), self.baud_chosen.get())
        # print("UART OPEN, COM {}, baud {}".format(self.comm_port.get(), self.baud_input.get()))
        print("UART OPEN, COM {}, baud {}".format(self.port_chosen.get(), self.baud_chosen.get()))
        self.lines[1].set("UART OPEN, COM {}, baud {}".format(self.port_chosen.get(), self.baud_chosen.get()))

    def clear(self):
        for line in self.lines:
            line.set("")
        self.lines[0].set("ISD Operation Screen")

    @staticmethod
    def end():
        global running, ser
        running = 0
        if ser:
            ser.close()
        pass


def disp_msg_ID_RESPONSE(message):
    for line in esad_isd_gui.lines:
        line.set("")
    esad_isd_gui.lines[0].set("ISD Operation Screen")
    line_num = 1
    for line in message:
        esad_isd_gui.lines[line_num].set(str(line) + " : " + str(in_msg[line]))
        line_num += 1


def msg_CHKSUM(msg, mod=256):
    """Calculates message checksum so sum of all bits in message modulo given value is 0
    accepts byte array and a modulo number, default is 256"""
    checksum = mod - sum(msg) % mod
    # print("CHECKSUM: " + str(checksum))
    return checksum


def msg_ESAD_ISD_ID_COMMAND():
    """"Define Message ESAD ID COMMAND"""
    msg_Sync_Header = 0x75
    msg_Msg_ID = 0x39
    msg_Sub_Sys = 0x53
    msg_ID_Command = bytearray([msg_Sync_Header, msg_Msg_ID, msg_Sub_Sys])
    msg_CHSUM = msg_CHKSUM(msg_ID_Command)
    msg_ID_Command.append(msg_CHSUM)
    return msg_ID_Command


def msg_ESAD_SA_COMMAND():
    """Define Message ESAD S&A COMMAND"""
    msg_Sync_Header = 0x75
    msg_Msg_ID = 0xE6
    msg_set_SA_state_ARM = 0xB6
    msg_SA_Command = bytearray([msg_Sync_Header, msg_Msg_ID, msg_set_SA_state_ARM])
    msg_CHSUM = msg_CHKSUM(msg_SA_Command)
    msg_SA_Command.append(msg_CHSUM)
    return msg_SA_Command


def msg_ESAD_STATUS_REQ():
    """Define Message ESAD STATUS REQUEST"""
    msg_Sync_Header_stat = 0x75
    msg_Msg_ID_stat = 0xC4
    msg_STATUS_REQUEST = bytearray([msg_Sync_Header_stat, msg_Msg_ID_stat])
    msg_CHSUM = msg_CHKSUM(msg_STATUS_REQUEST)
    msg_STATUS_REQUEST.append(msg_CHSUM)
    return msg_STATUS_REQUEST


def msg_ESAD_ID_RESPONSE(msg):
    """Define Messade ESAD ID RESPONSE"""
    com_soft_ver_lsb = msg[2]
    com_soft_ver_msb = msg[3]
    sw_checksum = msg[4]
    pbit_results = {
        "RAM Check fail": bin(msg[5])[2],
        "ROM Check fail": bin(msg[5])[3],
        "Act Voltage existing": bin(msg[5])[4],
        "ID Incorrect": bin(msg[5])[5]
    }
    esad_type = "ISD" if msg[6] == 0x68 else "Invalid"
    return {"Communication SW version LSB": com_soft_ver_lsb,
            "Communication SW version MSB": com_soft_ver_msb,
            "SW CheckSum": sw_checksum,
            "PBIT Results": pbit_results,
            "ESAD Type": esad_type
            }


def msg_ESAD_STATUS_RESP(msg):
    global in_msg
    """Define Message ESAD STATUS RESPONSE"""
    if msg[2] == 0xE6:
        request_command = "ESAD S&A Command"
    elif msg[2] == 0xC4:
        request_command = "ESAD Status Request"
    else:
        request_command = "Invalid"
    comm_errors = {
        "Parity Error": bin(msg[3])[0],
        "Framing Error": bin(msg[3])[1],
        "Noise Error": bin(msg[3])[2],
        "Overrun Error": bin(msg[3])[3],
        "Checksum Error": bin(msg[3])[4],
    }
    cont_bit = {
        "FIRE UNIT RAM Fail": bin(msg[4])[0],
        "FIRE UNIT ROM Fail": bin(msg[4])[1],
        "FIRE UNIT I/O Fail": bin(msg[4])[2],
        "DUD Status": bin(msg[4])[5],
    }
    if bin(msg[4])[6:8] == 0b00:
        esad_safe_stat = "SAFE"
    elif bin(msg[4])[6:8] == 0b01:
        esad_safe_stat = "NOT SAFE"
    elif bin(msg[4])[6:8] == 0b10:
        esad_safe_stat = "ARM"
    else:
        esad_safe_stat = "UNKNOWN"
    main_cpu_logic_state = ESAD_LOGIC_STATES[msg[5]]
    fire_cap_voltage = msg[6]
    return {
        "request_command": request_command,
        "Connunication Errors": comm_errors,
        "CBIT Results": cont_bit,
        "ESAD Safe Status": esad_safe_stat,
        "CPU Logic State": main_cpu_logic_state,
        "Fire Cap Voltage": fire_cap_voltage
    }


def rec_msg_handling(rec_msg):
    global in_msg
    """handling with received messages, accepts lists"""
    if rec_msg[0] == 0x75:  # Message valid Sync Header
        # if not msg_CHKSUM(rec_msg): pass
        if rec_msg[1] == 0x47:
            print("received ID Response Message")
            in_msg = msg_ESAD_ID_RESPONSE(rec_msg)
            disp_msg_ID_RESPONSE(in_msg)
        if rec_msg[1] == 0x39:
            print("ECHO ID Message")  # ID Message Echo
        if rec_msg[1] == 0xE6:
            print("ECHO S&A Command Message")  # S&A Command Message Echo
        if rec_msg[1] == 0xC4:
            print("ECHO Status Request Message")  # Status Request Message Echo
        if rec_msg[1] == 0xD3:
            print("received Status Response message")
            in_msg = msg_ESAD_STATUS_RESP(rec_msg)
            disp_msg_ID_RESPONSE(in_msg)
    else:
        pass


def open_uart_port(port="COM1", baud=9600, time_out=0):
    """"Opens UART protocol port"""
    global ser
    ser = serial.Serial(port, baud, timeout=time_out, stopbits=1, bytesize=8, parity="N")
    # ser.rs485_mode = serial.rs485.RS485Settings()


def send_UART_message(message):
    """"Send over UART a selectd message"""
    global ser
    print(time())
    print("out: " + str(list(message)))
    ser.write(message)
    sleep(0.05)
    read_uart_message()


def read_uart_message():
    """read from UART"""
    global ser
    msg = ser.read(100)
    print("in: " + str(list(msg)))
    # msg = list(ser2.read())  # Testing ONLY!!!!
    if len(msg):
        rec_msg_handling(msg)
    else:
        print('No Message received')


def send_ESAD_ISD_ID_COMMAND():
    """Send message over UART"""
    msg_to_send = msg_ESAD_ISD_ID_COMMAND()
    # msg_to_send = b'ESAD_ISD_ID_COMMAND'  # TESTING ONLY!!!
    send_UART_message(msg_to_send)


def send_ESAD_STATUS_REQ():
    """Send message over UART"""
    msg_to_send = msg_ESAD_STATUS_REQ()
    # msg_to_send = b'ESAD_STATUS_REQ'  # TESTING ONLY!!!
    send_UART_message(msg_to_send)


def send_ESAD_SA_COMMAND():
    """Send message over UART"""
    msg_to_send = msg_ESAD_SA_COMMAND()
    # msg_to_send = b'ESAD_SA_COMMAND'  # TESTING ONLY!!!
    send_UART_message(msg_to_send)


def status_req_task():
    global running, ser
    if ser and not running:
        running = 1
        task_send_STAT(top)
    # master.after(100, printTime, master)
    # send_ESAD_STATUS_REQ()


def task_send_STAT(master):
    if running:
        master.after(100, task_send_STAT, master)
        send_ESAD_STATUS_REQ()
    else:
        esad_isd_gui.lines[1].set("Stop sending STATUS Requests")


def main():
    global esad_isd_gui, top
    # Init
    top = Tk()
    esad_isd_gui = esad_gui(top)
    top.mainloop()


if __name__ == '__main__':
    main()

