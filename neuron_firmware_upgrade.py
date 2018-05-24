#!/usr/bin/python
# -*- coding: utf-8 -*

from time import sleep
import serial
import serial.tools.list_ports
import re
import sys
import getopt
import threading
from threading import Timer
import random
import os
import codecs, binascii
#import msvcrt
from struct import pack, unpack

FRAME_HEAD = 0xf0
FRAME_END = 0xf7

NO_VALID_FRAME          = 0
FRAME_HEAD_START        = 1

isResponse = False
timeCount = 0
failed_to_exit = False
update_completed = False
file_path = None
serialName = "COM4"
device_id = 1

responses_result_dict = dict() 

def send_BYTE(checksum, data):
    data_bytes = bytearray()
    checksum = (checksum + data) & 0x7f
    data_bytes.append(data & 0x7f)
    return checksum, data_bytes

def send_byte(checksum, data):
    data_bytes = bytearray()
    input_data_to_bytes = pack('B', data)
    data1 = ord(input_data_to_bytes[0]) & 0x7f
    data2 = (ord(input_data_to_bytes[0]) >> 7) & 0x7f

    data_bytes.append(data1)
    checksum = (checksum + data1) & 0x7f
    data_bytes.append(data2)
    checksum = (checksum + data2) & 0x7f
    return checksum, data_bytes

def send_SHORT(checksum, data):
    data_bytes = bytearray()

    input_data_to_bytes = pack('h', data)
    data1 = ord(input_data_to_bytes[0]) & 0x7f
    data2 = ((ord(input_data_to_bytes[1]) << 1) + (ord(input_data_to_bytes[0]) >> 7)) & 0x7f

    data_bytes.append(data1)
    checksum = (checksum + data1) & 0x7f
    data_bytes.append(data2)
    checksum = (checksum + data2) & 0x7f
    return checksum, data_bytes

def send_short(checksum, data):
    data_bytes = bytearray()

    input_data_to_bytes = pack('h', data)
    data1 = ord(input_data_to_bytes[0]) & 0x7f
    data2 = ((ord(input_data_to_bytes[1]) << 1) + (ord(input_data_to_bytes[0]) >> 7)) & 0x7f
    data3 = (ord(input_data_to_bytes[1]) >> 6) & 0x7f

    data_bytes.append(data1)
    checksum = (checksum + data1) & 0x7f
    data_bytes.append(data2)
    checksum = (checksum + data2) & 0x7f
    data_bytes.append(data3)
    checksum = (checksum + data3) & 0x7f
    return checksum, data_bytes

def send_float(checksum, data):
    data_bytes = bytearray()
    input_data_to_bytes = pack('f', data)
    data1 = ord(input_data_to_bytes[0]) & 0x7f
    data2 = ((ord(input_data_to_bytes[1]) << 1) + (ord(input_data_to_bytes[0]) >> 7)) & 0x7f
    data3 = ((ord(input_data_to_bytes[2]) << 2) + (ord(input_data_to_bytes[1]) >> 6)) & 0x7f
    data4 = ((ord(input_data_to_bytes[3]) << 3) + (ord(input_data_to_bytes[2]) >> 5)) & 0x7f
    data5 = (ord(input_data_to_bytes[3]) >> 4) & 0x7f

    data_bytes.append(data1)
    checksum = (checksum + data1) & 0x7f
    data_bytes.append(data2)
    checksum = (checksum + data2) & 0x7f
    data_bytes.append(data3)
    checksum = (checksum + data3) & 0x7f
    data_bytes.append(data4)
    checksum = (checksum + data4) & 0x7f
    data_bytes.append(data5)
    checksum = (checksum + data5) & 0x7f
    return checksum, data_bytes

def send_long(checksum, data):
    data_bytes = bytearray()
    input_data_to_bytes =  pack('l', data)
    data1 = ord(input_data_to_bytes[0]) & 0x7f
    data2 = ((ord(input_data_to_bytes[1]) << 1) + (ord(input_data_to_bytes[0]) >> 7)) & 0x7f
    data3 = ((ord(input_data_to_bytes[2]) << 2) + (ord(input_data_to_bytes[1]) >> 6)) & 0x7f
    data4 = ((ord(input_data_to_bytes[3]) << 3) + (ord(input_data_to_bytes[2]) >> 5)) & 0x7f
    data5 = (ord(input_data_to_bytes[3]) >> 4) & 0x7f

    data_bytes.append(data1)
    checksum = (checksum + data1) & 0x7f
    data_bytes.append(data2)
    checksum = (checksum + data2) & 0x7f
    data_bytes.append(data3)
    checksum = (checksum + data3) & 0x7f
    data_bytes.append(data4)
    checksum = (checksum + data4) & 0x7f
    data_bytes.append(data5)
    checksum = (checksum + data5) & 0x7f
    return checksum, data_bytes

def send_crc_long(checksum, data):
    data_bytes = bytearray()
    input_data_to_bytes =  pack('L', data)
    data1 = ord(input_data_to_bytes[0]) & 0x7f
    data2 = ((ord(input_data_to_bytes[1]) << 1) + (ord(input_data_to_bytes[0]) >> 7)) & 0x7f
    data3 = ((ord(input_data_to_bytes[2]) << 2) + (ord(input_data_to_bytes[1]) >> 6)) & 0x7f
    data4 = ((ord(input_data_to_bytes[3]) << 3) + (ord(input_data_to_bytes[2]) >> 5)) & 0x7f
    data5 = (ord(input_data_to_bytes[3]) >> 4) & 0x7f

    data_bytes.append(data1)
    checksum = (checksum + data1) & 0x7f
    data_bytes.append(data2)
    checksum = (checksum + data2) & 0x7f
    data_bytes.append(data3)
    checksum = (checksum + data3) & 0x7f
    data_bytes.append(data4)
    checksum = (checksum + data4) & 0x7f
    data_bytes.append(data5)
    checksum = (checksum + data5) & 0x7f
    return checksum, data_bytes

def usage():
    print 'neuron_firmware_upgrade.py usage:'
    print '-h, --help: Print help message.'
    print '-p, --port: Serial port for upgrade'
    print '-d, --device id: device id for module that need be upgrade'
    print '-i, --input: Firmware file input'

def assign_id_command(serial, retransmission_times = 3):
    global responses_result_dict
    global timeCount
    global failed_to_exit
    res = None
    comannd = bytearray([0xf0,0xff,0x10,0x00,0x0f,0xf7])
    responses_result_dict["assign_id"] = []
    responses_result_dict["universal_response"] = []
    print "assign_id_command"
    serial.write(comannd)
    timeCount = 0
    number_of_retransmissions = 0
    while(len(responses_result_dict["assign_id"]) < 2):
        if timeCount > 10:
            number_of_retransmissions = number_of_retransmissions + 1
            timeCount = 0
            print "retransmissions:" + str(number_of_retransmissions)
            serial.write(comannd)
        if number_of_retransmissions > retransmission_times:
            break
    print responses_result_dict["assign_id"]
    if len(responses_result_dict["assign_id"]) > 1:
        res = []
        res.append(responses_result_dict["assign_id"][0])
        res.append(responses_result_dict["assign_id"][1])
        res.append(responses_result_dict["assign_id"][2])
    return res

def set_the_module_enter_upgrade_mode(serial, dev_id, type, subtype):
    comannd = bytearray()
    comannd.append(FRAME_HEAD)
    comannd.append(dev_id)
    comannd.append(0x61)
    comannd.append(0x05)
    comannd.append(type)
    comannd.append(subtype)
    checksum = 0 
    for i in range(1,6):
        checksum += comannd[i] & 0x7f
    checksum = checksum & 0x7f
    comannd.append(checksum)
    comannd.append(FRAME_END)
    responses_result_dict["universal_response"] = []
    serial.write(comannd)

def mycrc32(data_bytes):
    m_pdwCrc32Table = [0 for x in range(0,256)]
    dwPolynomial = 0xedb88320L;
    dwCrc = 0
    for i in range(256):
       dwCrc = i
       for j in range(8):
           if dwCrc & 1:
               dwCrc = (dwCrc >> 1) ^ dwPolynomial
           else:
               dwCrc = (dwCrc >> 1)
       m_pdwCrc32Table[i] = dwCrc
    dwCrc32 = 0xFFFFFFFFL
    for ord_data in data_bytes:
        b = ord_data & 0x000000FFL
        dwCrc32 = m_pdwCrc32Table[(b ^ dwCrc32) & 0x000000FFL] ^ ((dwCrc32 >> 8) & 0x00FFFFFFL);
    dwCrc32 = dwCrc32 ^ 0xFFFFFFFFL
    #print 'dwCrc32: 0x%x' %(dwCrc32)
    return dwCrc32

def send_header(serial, dev_id, ord_data, retransmission_times = 3):
    global responses_result_dict
    global timeCount
    global failed_to_exit
    res = None
    data_len = len(ord_data)   #文件大小
    send_file_head_data = bytearray()
    checksum = 0
    send_file_head_data.append(FRAME_HEAD)
    send_file_head_data.append(dev_id)
    checksum = (checksum + dev_id) & 0x7f
    send_file_head_data.append(0x61)
    checksum = (checksum + 0x61) & 0x7f
    send_file_head_data.append(0x07)
    checksum = (checksum + 0x07) & 0x7f

    checksum, SHORT_bytes = send_SHORT(checksum, 0x0000)
    for byte in SHORT_bytes:
        send_file_head_data.append(byte)

    checksum, long_bytes = send_long(checksum, data_len)
    for byte in long_bytes:
        send_file_head_data.append(byte)

    crc_data = mycrc32(ord_data)
    checksum, long_bytes = send_crc_long(checksum, crc_data)
    for byte in long_bytes:
        send_file_head_data.append(byte)

    send_file_head_data.append(checksum)
    send_file_head_data.append(FRAME_END)
    responses_result_dict["send_head"] = []
    responses_result_dict["universal_response"] = []
    serial.write(send_file_head_data)

    timeCount = 0
    number_of_retransmissions = 0
    while(len(responses_result_dict["send_head"]) < 2):
        if timeCount > 100:
            number_of_retransmissions = number_of_retransmissions + 1
            timeCount = 0
            print "retransmissions:" + str(number_of_retransmissions)
            serial.write(send_file_head_data)
        if number_of_retransmissions > retransmission_times:
            failed_to_exit = True
            break

    if len(responses_result_dict["send_head"]) > 1:
        res = []
        res.append(responses_result_dict["send_head"][0])
        res.append(responses_result_dict["send_head"][1])

    return res

def send_file_data_frame(serial, dev_id, frame_num, ord_data_frame, retransmission_times = 3):
    global responses_result_dict
    global timeCount
    global failed_to_exit
    res = None

    data_len = len(ord_data_frame)   #文件大小
    send_data_frame = bytearray()
    checksum = 0
    send_data_frame.append(FRAME_HEAD)
    send_data_frame.append(dev_id)
    send_data_frame.append(0x61)
    send_data_frame.append(0x07)

    checksum, SHORT_bytes = send_SHORT(checksum, frame_num + 1)
    for byte in SHORT_bytes:
        send_data_frame.append(byte)

    checksum, SHORT_bytes = send_SHORT(checksum, data_len * 2)
    for byte in SHORT_bytes:
        send_data_frame.append(byte)

    for ord_data in ord_data_frame:
        checksum, long_bytes = send_byte(checksum, ord_data)
        for byte in long_bytes:
            send_data_frame.append(byte)

    checksum = 0
    for i in range(1,(data_len * 2 + 8)):
        checksum = (checksum + send_data_frame[i]) & 0x7f
    send_data_frame.append(checksum)
    send_data_frame.append(FRAME_END)
    responses_result_dict["send_data_frame"] = []
    responses_result_dict["universal_response"] = []
    serial.write(send_data_frame)

    timeCount = 0
    number_of_retransmissions = 0
    while(len(responses_result_dict["send_data_frame"]) < 2):
        if timeCount > 20:
            number_of_retransmissions = number_of_retransmissions + 1
            timeCount = 0
            print "retransmissions:" + str(number_of_retransmissions)
            serial.write(send_data_frame)
        if number_of_retransmissions > retransmission_times:
            failed_to_exit = True
            break

    if len(responses_result_dict["send_data_frame"]) > 1:
        res = []
        res.append(responses_result_dict["send_data_frame"][0])
        res.append(responses_result_dict["send_data_frame"][1])
    return res

def check_update_status(serial, dev_id, retransmission_times = 3):
    global responses_result_dict
    global timeCount
    global failed_to_exit
    res = None
    comannd = bytearray([0xf0,0x01,0x61,0x08,0x00,0xf7])
    comannd[1] = dev_id
    checksum = 0
    for i in range(1,len(comannd)-2):
        checksum = (checksum + comannd[i]) & 0x7f
    comannd[4] = checksum
    responses_result_dict["check_update_status"] = []
    responses_result_dict["universal_response"] = []
    serial.write(comannd)

    timeCount = 0
    number_of_retransmissions = 0
    while(len(responses_result_dict["check_update_status"]) < 2):
        if timeCount > 20:
            number_of_retransmissions = number_of_retransmissions + 1
            timeCount = 0
            print "retransmissions:" + str(number_of_retransmissions)
            serial.write(comannd)
        if number_of_retransmissions > retransmission_times:
            failed_to_exit = True
            break

    if len(responses_result_dict["check_update_status"]) > 1:
        res = []
        res.append(responses_result_dict["check_update_status"][0])
        res.append(responses_result_dict["check_update_status"][1])
    return res

def reset_module(serial, dev_id):
    comannd = bytearray([0xf0,0x01,0x11,0x00,0xf7])
    comannd[1] = dev_id
    checksum = 0
    for i in range(1,len(comannd)-2):
        checksum = (checksum + comannd[i]) & 0x7f
    comannd[3] = checksum
    responses_result_dict["reset"] = []
    responses_result_dict["universal_response"] = []
    serial.write(comannd)

def set_codey_online(serial):
    comannd = bytearray([0xf3,0xf6,0x03,0x00,0x0d,0x00,0x01,0x0e,0xf4])
    serial.write(comannd)
    sleep(2)

def transfer_file(serial,dev_id = 0x01):
    global update_completed
    global file_path
    global failed_to_exit
    result = None
    if file_path == None:
        failed_to_exit = True
        print "The file path is not set!"
    else:
        try:
            myfile=open(file_path,'rb')
            data=myfile.read()
            ord_data = map(ord, data)
            myfile.close()
            file_size = len(ord_data)
            frame_num = 0
            send_header(serial, dev_id, ord_data)
            for i in range(0,file_size,64):
                frame_num = i/64
                if (file_size % 64 != 0) and (file_size/64 == frame_num):
                    ord_data_frame = ord_data[i:]
                    for i in range(64 - (file_size % 64)):
                        ord_data_frame.append(0x00)
                else:
                    ord_data_frame = ord_data[i:i+64]
                send_file_data_frame(serial, dev_id, frame_num, ord_data_frame)
            
            result = check_update_status(serial, dev_id)
            if result == None or result[1] == 0x00:
                print "firmware update failed!"
                update_completed = True
            else:
                print "firmware update success!"
                reset_module(serial, dev_id)
                update_completed = True
        except IOError:
            print('Error:Failed to find file or read file!')



def firmware_update():
    global serialFd
    global device_id
    global responses_result_dict
    responses_result_dict["assign_id"] = []
    responses_result_dict["send_head"] = []
    responses_result_dict["send_data_frame"] = []
    responses_result_dict["check_update_status"] = []
    responses_result_dict["reset"] = []
    responses_result_dict["universal_response"] = []
    is_module_in_bootloader = False
    res_assign_id = None

    if device_id != 1:
        set_codey_online(serialFd)
 
    print "update firmware for device:"
    print device_id
    while is_module_in_bootloader == False:
        res_assign_id = assign_id_command(serialFd)
        if(res_assign_id != None):
            if (res_assign_id[1] == 0x00) and (res_assign_id[2] == 0x00):
                is_module_in_bootloader = True
                if res_assign_id[0] == device_id:
                    print "module is in bootloader mode!"
                    transfer_file(serialFd, device_id)
                    break
                else:
                    print "the device id(" + str(device_id) + ") is not online"
            else:
                print "dev_id: 0x%x, type: 0x%x, subtype: 0x%x" %(res_assign_id[0],res_assign_id[1],res_assign_id[2])
                set_the_module_enter_upgrade_mode(serialFd,res_assign_id[0],res_assign_id[1],res_assign_id[2])
                sleep(0.02)
        else:
            sleep(1)
            print "No neuron module inserted!"

def process_neurons_responses(neuron_data_frame):
    global responses_result_dict
    global device_id
    if neuron_data_frame[1] == device_id:
        if neuron_data_frame[2] == 0x10:
            responses_result_dict["assign_id"] = []
            responses_result_dict["assign_id"].append(neuron_data_frame[1])
            responses_result_dict["assign_id"].append(neuron_data_frame[3])
            responses_result_dict["assign_id"].append(neuron_data_frame[4])

        elif neuron_data_frame[2] == 0x15:
            responses_result_dict["universal_response"] = []
            responses_result_dict["universal_response"].append(neuron_data_frame[1])
            responses_result_dict["universal_response"].append(neuron_data_frame[3])

        elif neuron_data_frame[2] == 0x61 and neuron_data_frame[3] == 0x08:
            responses_result_dict["check_update_status"] = []
            responses_result_dict["check_update_status"].append(neuron_data_frame[1])
            responses_result_dict["check_update_status"].append(neuron_data_frame[4])

        elif neuron_data_frame[2] == 0x61 and neuron_data_frame[3] == 0x07:
            if neuron_data_frame[4] == 0x00 and neuron_data_frame[5] == 0x00:
                responses_result_dict["send_head"] = []
                responses_result_dict["send_head"].append(neuron_data_frame[1])
                responses_result_dict["send_head"].append(neuron_data_frame[5])
            else:
                responses_result_dict["send_data_frame"] = []
                responses_result_dict["send_data_frame"].append(neuron_data_frame[1])
                responses_result_dict["send_data_frame"].append(neuron_data_frame[5])

def receive_task():
    global serialFd
    frame_status = NO_VALID_FRAME
    neuron_data_frame = bytearray()
    data_check_sum = 0
    while( True ):
        try:
            if(serialFd.inWaiting()):
                char_temp = serialFd.read(serialFd.inWaiting())
                ord_char_data = map(ord, char_temp)
                for i in range(len(ord_char_data)):
                    if frame_status == NO_VALID_FRAME:
                        if ord_char_data[i] == FRAME_HEAD:
                            neuron_data_frame.append(ord_char_data[i])
                            frame_status = FRAME_HEAD_START

                    elif frame_status == FRAME_HEAD_START:
                        neuron_data_frame.append(ord_char_data[i])
                        if(ord_char_data[i] == FRAME_END):
                            for i in range(1,len(neuron_data_frame) - 2):
                                data_check_sum = (data_check_sum + neuron_data_frame[i]) & 0x7f

                            if neuron_data_frame[-2] == data_check_sum:
                                process_neurons_responses(neuron_data_frame)
                                neuron_data_frame = bytearray()
                                data_check_sum = 0
                                frame_status = NO_VALID_FRAME
                            else:
                                neuron_data_frame = bytearray()
                                data_check_sum = 0
                                frame_status = NO_VALID_FRAME
            else:
                sleep(0.01)
        except IOError:
            print('Stop receive task!')

def timeCount_task():
    global timeCount
    while( True ):
        timeCount = timeCount + 1
        sleep(0.1)

def main():
    global serialName
    global serialFd
    global failed_to_exit
    global update_completed
    global file_path
    global device_id
    failed_to_exit = False
    update_completed = False
    opts, args = getopt.getopt(sys.argv[1:], "hp:i:d:")
    for op, value in opts: 
        if op == "-p": 
            serialName = value 
        elif op == "-i": 
            file_path = value
        elif op == "-d":
            device_id = int(value)
        elif op == "-h":
            usage()

    port_list = list(serial.tools.list_ports.comports())

    if len(port_list) <= 0:
        print "None Serial port been find!"
    else:
        timeCountTask = threading.Thread(target = timeCount_task)
        timeCountTask.setDaemon(True)  
        timeCountTask.start()
        for i in range(len(port_list)):
            port_list_0 = list(port_list[i])
            port_serial = port_list_0[0]
            if re.match(serialName, port_serial) != None:
                serialFd = serial.Serial(serialName, 115200, timeout = 0.1)
                firmwareUpdate = threading.Thread(target = firmware_update)
                firmwareUpdate.setDaemon(True)  
                firmwareUpdate.start()
                receiveTask = threading.Thread(target = receive_task)
                receiveTask.setDaemon(True)  
                receiveTask.start()
            else:
                print "The serial port[" + serialName + "] entered is incorrect!"

        while True:
            if failed_to_exit == True:
                sys.exit(1)
                break
            if update_completed == True:
                sys.exit(2)
                break
            # if ord(msvcrt.getch()) in [68, 100]:
            #     sys.exit(0)
            #     break

def _main():
    try:
        main()
    except SystemExit as ex:
        if str(ex) == '0':
            print '\r\nPress D/d to exit the script!'
        elif str(ex) == '1':
            print '\r\nTransmission abnormal exit!'
        elif str(ex) == '2':
            print '\r\nExit the firmware update script！'
        else:
            print '\r\nA fatal error occurred!'

if __name__ == '__main__':
    _main()