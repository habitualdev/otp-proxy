#!/usr/bin/python

# Simple tcp proxy that changes the external port that is open based off of a OTP

import os.path
import socket
import select
import time
import sys
import pyotp
import qrcode
import PIL

# Changing the buffer_size and delay, you can improve the speed and bandwidth.
# But when buffer get to high or delay go too down, you can break things
buffer_size = 4096
delay = 0.0001

# Default set to forward to SSH, but proxy is "dumb" enough it should work for anything
forward_to = ('127.0.0.1', 22)

class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception:
            return False

class TheServer:
    input_list = []
    channel = {}

    def __init__(self, host, port, seed):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.settimeout(1)
        self.server.setblocking(0)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)
        self.totp = pyotp.TOTP(seed)

    def main_loop(self, totp):
        self.input_list.append(self.server)
        totp_saved = totp.now()
        while True:
            time.sleep(delay)
            ss = select.select
            self.server.settimeout(1)
            timeout = self.server.gettimeout()
            inputready, outputready, exceptready = ss(self.input_list, [], [], float(.1))
            for self.s in inputready:
                if self.s == self.server:
                    self.on_accept()
                    break
                self.data = self.s.recv(buffer_size)
                if len(self.data) == 0:
                    self.on_close()
                    break
                else:
                    self.on_recv()
            if totp_saved != totp.now():
                break


    def on_accept(self):
        forward = Forward().start(forward_to[0], forward_to[1])
        clientsock, clientaddr = self.server.accept()
        if forward:
            print(clientaddr, "has connected")
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock
        else:
            print("Can't establish connection with remote server.",)
            print("Closing connection with client side", clientaddr)
            clientsock.close()

    def on_close(self):
        print(self.s.getpeername(), "has disconnected")
        #remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[self.s]


    def on_recv(self):
        data = self.data
        # here we can parse and/or modify the data before send forward
        #print(data)
        self.channel[self.s].send(data)

if __name__ == '__main__':
    # Seed can be changed to anything.
    seed = "LongRandomString"
    otp_outer = pyotp.TOTP(seed)
    qr_data = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4,)
    qr_data.add_data(otp_outer.provisioning_uri(name="roaldi@github.com", issuer_name="Proxy OTP"))
    qr_data.make(fit=True)
    qr_img = qr_data.make_image()
    qr_img.save("qrcode.jpg")
    while True:

        otp_num = str(otp_outer.now())[-4:]
        server = TheServer('', int(otp_num), seed)

        try:
            server.main_loop(server.totp)

        except KeyboardInterrupt:
            print("Ctrl C - Stopping server")
            sys.exit(1)
