import os
import socket
import sys
import time

def build_frame(message):
    framesize = len(message)
    s_frame = chr(0x80) + chr(0x00) + chr((framesize >> 8) & 0xFF) + chr(framesize & 0xFF) + message
    return s_frame

def receive_func():
    amount_expected = 6
    amount_received = 0
    while amount_received < amount_expected:
        data = sock.recv(50)
        amount_received += len(data)
    return data

def menu():

    repeat_menu = True
    while repeat_menu:
        os.system('cls')
        print("Options:")
        print("1-Read Voltage")
        print("2-Exit")

        option = input("Insert option >> ")
        if int(option)<1 or int(option) > 2:
            print("Not valid option")
            time.sleep(2)
        else:
            break
    return option    
    
if __name__ == '__main__':
    os.system('cls')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print('Enter IP Address: ')
    ip_address = input()
    print('Enter TCP Port:')
    tcp_port = int(input())
    server_address = (ip_address, tcp_port)

    sock.connect(server_address)
    sock.settimeout(2.0)

    print(receive_func())
    message = build_frame(input())
    sock.sendall(message)

    print(receive_func())
    message = build_frame(input())
    sock.sendall(message)

    print(receive_func())

    repeat_cycle = True
    while repeat_cycle:
        opt = menu()
        if opt == 2:
            repeat_cycle = False
        if opt == 1:
            message = build_frame(":NUMERIC:NORMAL:VALUE? 1")
            sock.sendall(message)
            dato = receive_func()
            print(dato)
        time.sleep(2)

    print >> sys.stderr, 'closing socket'
    sock.close()
