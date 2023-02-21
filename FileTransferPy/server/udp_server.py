import socket
import hashlib
import os
import subprocess
import time
from ks_functions import *


def ip_choice(list_of_ips):
    print("Welcome to FTA Rev")
    ip_to_bind = input("To begin would you like to bind to localhost (127.0.0.1) (Y/n)? ")
    if ip_to_bind.lower() == "y":
        ip = "localhost"
        print(f"Binding socket to {ip}...")
    else:
        print("Ohh you want to go online :) ")
        print("Here are a few options of IP addresses to bind: ")
        i = 1

        for address in list_of_ips:
            print(f"     {i}. {address[4][0]}")
            i += 1

        ip_chosen = int(input("Make a choice based on the number shown before each address: "))
        ip = list_of_ips[ip_chosen - 1][4][0]
        time.sleep(1)
        print(f"Binding socket to {ip}...")
    return ip


def sendEncrypt(plain_txt):
    global addr
    global client_pub_key
    cypher = encrypt_ks(plain_txt, client_pub_key)
    server_s.sendto(cypher.encode(), addr)


def receiveDecrypt():
    global addr
    global private_key
    global inverse_n
    global m
    msg, addr = server_s.recvfrom(1024 * 60)
    msg = decrypt_ks(msg.decode(), private_key, inverse_n, m)
    return msg


def find_pub_key(priv_key, m_value, n_value):
    public_key = []
    for value in priv_key:
        pub_key_val = (value * n_value) % m_value
        public_key.append(pub_key_val)
    return public_key


# keys
private_key = [2, 3, 6, 13, 27, 52, 105, 210]
n = 249
m = 419
pub_key = find_pub_key(private_key, m, n)
inverse_n = pow(n, -1, m)
sep = "<sep>"
remote_dir_active = False

name = socket.gethostname()
addrs = socket.getaddrinfo(name, None)
ip_socket = ip_choice(addrs)

# bind server
server_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
port = 9999
server_s.bind((ip_socket, port))
print("Server is up! Waiting on connection...")

# receive keys
message, addr = server_s.recvfrom(1024*2)
print("Connected:", addr[0])
message = message.decode()
client_pub_key = list(map(int, message.split(sep)))
print("Encryption Key Received!")

# send pub key
pub_key_string = ""
for idx in range(len(pub_key)):
    if idx == 7:
        pub_key_string += str(pub_key[idx])
    else:
        pub_key_string += str(pub_key[idx]) + sep

pubKey_cwd = pub_key_string + "#hereisCWD" + os.getcwd()
server_s.sendto(pubKey_cwd.encode(), addr)

while True:
    message = receiveDecrypt()
    print(f"Command Received: '{message}'")

    if message[0:4] == "put ":
        cmd_div = message.split()

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
        print("\nFile Hash:      ", client_hex)
        print("\nHash Generated: ", hex_dig)

        if client_hex != hex_dig:
            print("\n[!] Cannot confirm file is original. Deleting Now. [!]\n")
            sendEncrypt("[!]")
            os.remove(cmd_div[1])
        else:
            sendEncrypt("[.]")
            print("\n[.] File is original.")

    elif message[0:4] == "get ":
        cmd_split = message.split()
        with open(cmd_split[1], "r") as filehex:
            file_data = filehex.read()
            hash_object = hashlib.sha256(file_data.encode())
            hex_dig = hash_object.hexdigest()
            print(hex_dig)
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
            print("\n[!] Unable to upload file.\n")
        else:
            print("\nUpload Successful!\n")

    elif message == "exit":
        print("\nClosing Connection.")
        break

    elif message == "chdir":
        if remote_dir_active:
            remote_dir_active = False
        else:
            remote_dir_active = True

    elif message == "ls":
        file_list = os.listdir(os.getcwd())
        file_string = sep.join(file_list)
        sendEncrypt(file_string)

    elif message[0:4] == "cdr ":
        if remote_dir_active:
            splt = message.split()
            print(splt)
            try:
                os.chdir(splt[1])
                sendEncrypt(os.getcwd())
            except:
                print("No dir found.")
        else:
            sendEncrypt(os.getcwd())

    elif message[0:3] == "cd ":
        pass

    else:
        output = subprocess.getoutput(message)
        sendEncrypt(output)

server_s.close()
