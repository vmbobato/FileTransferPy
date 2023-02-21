import socket
import hashlib
import os
import time
import subprocess
from ks_functions import *


def ip_choice():
    valid = False
    IP_val = input("Enter IP (_._._._): ")
    while not valid:
        ip_list = IP_val.split(".")
        if len(ip_list) == 4:
            i = 0
            for value in ip_list:
                try:
                    int(value)
                    i += 1
                except ValueError:
                    continue
            if i == 4:
                print("Thank you, connecting now...")
                valid = True
            else:
                IP_val = input("Not valid format, try again: ")
        else:
            IP_val = input("Not valid format, try again: ")
    return IP_val


def sendEncrypt(plain_txt):
    global addr
    global server_pub_key
    cypher = encrypt_ks(plain_txt, server_pub_key)
    s.sendto(cypher.encode(), addr)


def receiveDecrypt():
    global addr
    global private_key
    global inverse_n
    global m
    msg, addr = s.recvfrom(1024 * 60)
    msg = decrypt_ks(msg.decode(), private_key, inverse_n, m)
    return msg


def find_pub_key(private_key):
    global n
    global m
    public_key = []
    for value in private_key:
        pub_key_val = (value * n) % m
        public_key.append(pub_key_val)
    return public_key


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
port = 9999
sep = "<sep>"

private_key = [2, 7, 11, 21, 42, 89, 180, 354]
n = 588
m = 881
pub_key = find_pub_key(private_key)
inverse_n = pow(n, -1, m)

print("\nWelcome to FTA Rev")
print("You will be offered a command line to download and upload files to a remote server. ")
print("You will also be able to navigate through your machine and the remote machine with commands similar")
print("to Linux/UNIX systems. REMINDER this application is case sensitive!")
print("\nType 'h' or 'help' for help on the commands.\n")
print("But first input an IP address of the server to connect to...")

ip = ip_choice()
time.sleep(1)
# Include the server Address
serverAddr = (ip, port)

# send pub key
pub_key_string = ""
for idx in range(len(pub_key)):
    if idx == 7:
        pub_key_string += str(pub_key[idx])
    else:
        pub_key_string += str(pub_key[idx]) + sep

s.sendto(pub_key_string.encode(), serverAddr)
print(f"Connected to: {ip}")
print("Accessing CLI...")

time.sleep(0.7)

# receive server key
message, addr = s.recvfrom(1024*2)
message = message.decode()
cwd_key = message.split("#hereisCWD")
remote_dir = cwd_key[1]
server_pub_key = list(map(int, cwd_key[0].split(sep)))
remote_dir_active = False

while True:

    if not remote_dir_active:
        directory = os.getcwd()
    else:
        directory = remote_dir

    command = input(f"\n{directory}>$ ")
    sendEncrypt(command)

    if command[0:4] == "get ":
        cmd_div = command.split()

        with open(cmd_div[1], "w") as file:
            while True:
                content = receiveDecrypt()
                if not content:
                    file.write(content)
                    break
                file.write(content)
            file.close()

        with open(cmd_div[1], "r") as file2:
            content = file2.read()
            file2.close()
            hash_object = hashlib.sha256(content.encode())
            hex_dig = hash_object.hexdigest()
            file2.close()

        client_hex = receiveDecrypt()
        print("\nFile Hash Received:        ", client_hex)
        print("\nHash Generated (SHA 256):  ", hex_dig)

        if client_hex != hex_dig:
            sendEncrypt("[!]")
            decision = input("\n[!] Cannot confirm file is safe. Delete it (Y/n)? ")
            if decision.lower() == "y":
                try:
                    os.remove(cmd_div[1])
                    print("\n[.] File has been deleted.")
                except FileNotFoundError:
                    print("\n[!] File can't be deleted. Try again later.")
            else:
                print("\nOkay... File will not be deleted.")
        else:
            sendEncrypt("[.]")
            print("\n[.] File Download Successful.")

    elif command[0:4] == "put ":
        cmd_split = command.split()
        with open(cmd_split[1], "r") as filehex:
            file_data = filehex.read()
            hash_object = hashlib.sha256(file_data.encode())
            hex_dig = hash_object.hexdigest()
            filehex.close()

        with open(cmd_split[1], "r") as file:
            while True:
                content = file.read(1024)
                if not content:
                    sendEncrypt(content)
                    break
                sendEncrypt(content)
            file.close()
        sendEncrypt(hex_dig)
        confirmation = receiveDecrypt()

        if confirmation == "[!]":
            print("\n[!] Unable to upload file. Server could not confirm whether file is original.")
        else:
            print("\n[.] Upload Successful!")

    elif command == "exit":
        sendEncrypt(command)
        print("\nClosing connection...")
        time.sleep(2)
        print("\n[.] Done!")
        sendEncrypt(command)
        break

    elif command == "chdir":
        print("\nChanging machine file system...")
        if remote_dir_active:
            remote_dir_active = False
        else:
            remote_dir_active = True
        print("\nDone!")

    elif command == "ls":
        if remote_dir_active:
            print()
            file_str = receiveDecrypt()
            file_list = file_str.split(sep)
            i = 1
            for files in file_list:
                print(f"{i}. {files}")
                i += 1
        else:
            file_list = os.listdir(os.getcwd())
            i = 1
            print()
            for files in file_list:
                print(f"{i}. {files}")
                i += 1

    elif command[0:3] == "cd ":
        if remote_dir_active:
            print("\n[!] Remote Dir Active, to navigate in your machine deactivate remote dir.")
            pass
        else:
            cmd = command.split()
            try:
                os.chdir(cmd[1])
            except:
                print("\n[!] No Dir Found!")

    elif command[0:4] == "cdr ":
        if remote_dir_active:
            output = receiveDecrypt()
            remote_dir = output
        else:
            print("\n[!] Remote machine Not active")

    elif command.lower() == "help" or command.lower() == "h":
        print("""\nThe commands for the application:\n
        - put ___ : upload a file to the server.
        - get ___ : download file from server.
        - ls      : list contents of current directory.
        - chdir   : change in between machines.
        - cdr ___ : change directory. (only works when working on the remote machine)
        - cd ____ : change directory. (only when working on your machine)
        - exit    : close application on both sides.""")

    else:
        output = receiveDecrypt()
        print("\n" + output)

s.close()
