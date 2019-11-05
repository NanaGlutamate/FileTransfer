import socket
import os
import hashlib
import getpass
import get_ip


class FileTransferServer:
    def __init__(self):
        self.addr = None
        self.c = None
        self.cache = ''
        while True:
            pwd1 = hashlib.new('md5', bytes(getpass.getpass('set passport:'), encoding='utf8')).hexdigest()
            pwd2 = hashlib.new('md5', bytes(getpass.getpass('set passport again:'), encoding='utf8')).hexdigest()
            if pwd1 == pwd2:
                self.passport = bytes(pwd1, encoding='utf8')
                print('passport set.')
                break
            else:
                print('not inherent, entry again.')
        self.s = socket.socket(socket.AF_INET)
        self.host = get_ip.get_ip()
        self.port = 54320
        for i in range(40):
            try:
                self.port += 1
                self.s.bind((self.host, self.port))
                break
            except socket.error:
                continue
        print('local host: '+self.host+':'+str(self.port))
        print('start listening.')
        self.listen()

    def listen(self):
        self.s.listen(2)
        while True:
            self.c, self.addr = self.s.accept()
            print(self.addr[0]+':'+str(self.addr[1])+' connected.')
            pwd = self.c.recv(1024)
            if pwd != self.passport:
                print(self.addr[0]+':'+str(self.addr[1])+' entry wrong passport.')
                self.c.shutdown(2)
                self.c.close()
                continue
            print(self.addr[0]+':'+str(self.addr[1])+' entry correct passport.')
            self.c.send(b'welcome')
            self.service()

    def service(self):
        while True:
            command = str(self.c.recv(1024), 'utf8')
            print(self.addr[0]+':'+str(self.addr[1])+'>>'+('*NULL*' if command == '' else command))
            if command == '':
                print(self.addr[0]+':'+str(self.addr[1])+' offline.')
                break
            elif command[0:3] == 'CD ':
                self.cd_dir(command[3:])
            elif command[0:3] == 'DL ':
                self.send(command[3:])
            elif command[0:3] == 'UL ':
                self.recv(command[3:])

    def cd_dir(self, path):
        if not os.path.isdir(path):
            self.c.send(bytes(self.cache, 'utf8'))
            return
        os.chdir(path)
        new_list = os.listdir('./')
        new_listdir = []
        new_filedir = []
        for i in range(len(new_list)):
            if os.path.isdir(new_list[i]):
                new_listdir.append('+' + new_list[i])
            else:
                new_filedir.append('`' + new_list[i])
        self.cache = str(['../'] + new_listdir + new_filedir)[1:-1]
        self.c.send(bytes(self.cache, 'utf8'))
        return

    def send(self, name):
        if not os.path.isfile(name):
            self.c.send(b'NOT_FILE')
            return
        size = os.path.getsize(name)
        command = b'S-'+bytes(name, 'utf8')+bytes(':'+str(size), 'utf8')
        if len(command) >= 1023:
            self.c.send(b'TOO_LONG')
            return
        self.c.send(command)
        reply = self.c.recv(128)
        if reply != b'READY':
            print('transfer failed, client error.')
            return
        with open(name, 'rb') as f:
            s = f.read()
            self.c.send(s+bytes(hashlib.new('md5', s).hexdigest(), 'utf8'))
        reply = self.c.recv(128)
        if reply == b'CORRECT':
            return
        elif reply == b'WRONG':
            print('transfer failed, connection not stable.')
            return
        else:
            print('transfer failed, reply not correct.')
            return

    def recv(self, name_size):
        name, size = name_size.split(':')
        size = int(size)
        if os.path.exists(name):
            self.c.send(b'CONFLICT')
            return
        self.c.send(b'READY')
        s = self.c.recv(size+32)
        if s == b'':
            print("error in 'UL "+name_size+"'")
            return
        if s[-32:] == bytes(hashlib.new('md5', s[:-32]).hexdigest(), 'utf8'):
            self.c.send(b'CORRECT')
            with open(name, 'wb') as f:
                f.write(s[:-32])
        else:
            self.c.send(b'WRONG')


if __name__ == '__main__':
    FileTransferServer()
