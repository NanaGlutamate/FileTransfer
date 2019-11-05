import socket
from tkinter import *
import tkinter.messagebox
from tkinter.simpledialog import askstring
import os
import hashlib
import get_ip


class FileTransfer:
    def __init__(self):
        self.host = None
        self.s = None
        self.root = Tk()
        self.src = StringVar()
        self.tar = StringVar()
        self.command = StringVar()
        self.root.title('文件传输')
        self.menu = Menu(self.root)
        self.menu.add_command(label='未连接服务器', command=self.link)
        self.command_frame = Frame(self.root)
        self.target_list = Listbox(self.root, listvariable=self.tar)
        self.download_button = Button(self.root, text='下载', command=self.download)
        self.command_status = Listbox(self.command_frame, listvariable=self.command)
        self.scroll = Scrollbar(self.command_frame)
        self.scroll.config(command=self.command_status.yview)
        self.command_status.config(yscrollcommand=self.scroll.set)
        self.source_list = Listbox(self.root, listvariable=self.src)
        self.upload_button = Button(self.root, text='上传', command=self.upload)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.command_frame.columnconfigure(0, weight=1)
        self.command_frame.rowconfigure(0, weight=1)
        self.target_list.grid(row=0, column=0, sticky=W+N+S)
        self.download_button.grid(row=1, column=0, sticky=W+E)
        self.command_frame.grid(row=0, column=1, rowspan=2, sticky=W+E+N+S)
        self.command_status.grid(row=0, column=0, sticky=W+E+N+S)
        self.scroll.grid(row=0, column=1, sticky=N+S)
        self.source_list.grid(row=0, column=2, sticky=E+N+S)
        self.upload_button.grid(row=1, column=2, sticky=W+E)
        self.source_list.bind("<Double-Button-1>", self.goto_path)
        self.target_list.bind("<Double-Button-1>", self.get_path)
        self.goto_path(None)
        self.root.config(menu=self.menu)
        self.root.mainloop()

    def goto_path(self, flag=None):
        if not flag:
            s = './'
        else:
            s = self.source_list.get(self.source_list.curselection())
        if s != './' and s != '../':
            if not os.path.isdir(s[1:]):
                return
            os.chdir(s[1:])
        else:
            os.chdir(s)
        new_list = os.listdir('./')
        new_listdir = []
        new_filedir = []
        for i in range(len(new_list)):
            if os.path.isdir(new_list[i]):
                new_listdir.append('+' + new_list[i])
            else:
                new_filedir.append('`' + new_list[i])
        new_list = ['../'] + new_listdir + new_filedir
        self.src.set(tuple(new_list))

    def get_path(self, flag=None, record=True):
        if not flag:
            self.s.send(b'CD ./')
            s = './'
        else:
            s = self.target_list.get(self.target_list.curselection())
            if s != '../':
                s = s[1:]
            command = b'CD '+bytes(s, 'utf8')
            if len(command) >= 1023:
                if record:
                    self.command_status.insert(END, 'CD ' + s + ' ,failed')
                tkinter.messagebox.showerror(title='错误', message='文件名过长')
                return
            self.s.send(command)
        dir_recv = str(self.s.recv(10240), 'utf-8')
        l_dir = tuple(map(lambda x: x[1:-1], dir_recv.split(', ')))
        if record:
            self.command_status.insert(END, 'CD ' + s)
        self.tar.set(l_dir)

    def upload(self):
        name = self.source_list.get(self.source_list.curselection())[1:]
        if not os.path.isfile(name):
            self.command_status.insert(END, '<' + name + ' ,failed')
            tkinter.messagebox.showerror(title='错误', message='只能上传文件')
            return
        size = os.path.getsize(name)
        command = b'UL '+bytes(name, 'utf8')+bytes(':'+str(size), 'utf8')
        if len(command) >= 1023:
            self.command_status.insert(END, '<' + name + ' ,failed')
            tkinter.messagebox.showerror(title='错误', message='文件名过长')
            return
        self.s.send(command)
        reply = self.s.recv(128)
        if reply == b'CONFLICT':
            self.command_status.insert(END, '<' + name + ' ,failed')
            tkinter.messagebox.showerror(title='错误', message='文件名冲突')
            return
        if reply != b'READY':
            self.command_status.insert(END, '<' + name + ' ,failed')
            tkinter.messagebox.showerror(title='错误', message='服务器错误')
            return
        with open(name, 'rb') as f:
            s = f.read()
            self.s.send(s+bytes(hashlib.new('md5', s).hexdigest(), 'utf8'))
        reply = self.s.recv(128)
        if reply == b'CORRECT':
            self.get_path(None, record=False)
            self.command_status.insert(END, '<' + name)
            return
        elif reply == b'WRONG':
            self.command_status.insert(END, '<' + name + ' ,failed')
            tkinter.messagebox.showerror(title='错误', message='传输失败')
            return
        else:
            self.command_status.insert(END, '<' + name + ' ,failed')
            tkinter.messagebox.showerror(title='错误', message='服务器错误')
            return

    def download(self):
        name = self.target_list.get(self.target_list.curselection())
        if name[0] != '`':
            self.command_status.insert(END, '>' + name + ',failed')
            tkinter.messagebox.showerror(title='错误', message='只能下载文件')
            return
        name = name[1:]
        self.s.send(b'DL '+bytes(name, 'utf8'))
        name_size = self.s.recv(1024)
        if name_size[0:8] == b'NOT_FILE':
            self.command_status.insert(END, '>' + name + ',failed')
            tkinter.messagebox.showerror(title='错误', message='只能下载文件')
            return
        elif name_size[0:2] != b'S-':
            self.command_status.insert(END, '>' + name + ',failed')
            tkinter.messagebox.showerror(title='错误', message='服务器错误')
            self.s.send(b'ERROR')
            return
        name, size = str(name_size, 'utf8')[2:].split(':')
        size = int(size)
        if os.path.exists(name):
            self.command_status.insert(END, '>' + name + ',failed')
            tkinter.messagebox.showerror(title='错误', message='文件名冲突')
            self.s.send(b'CONFLICT')
            return
        self.s.send(b'READY')
        s = self.s.recv(size+32)
        if s == b'':
            self.command_status.insert(END, '>' + name + ',failed')
            tkinter.messagebox.showerror(title='错误', message='服务器连接错误')
            return
        if s[-32:] == bytes(hashlib.new('md5', s[:-32]).hexdigest(), 'utf8'):
            self.s.send(b'CORRECT')
            with open(name, 'wb') as f:
                f.write(s[:-32])
            self.goto_path(None)
            self.command_status.insert(END, '>' + name)
        else:
            self.command_status.insert(END, '>' + name + ',failed')
            self.s.send(b'WRONG')

    def link(self):
        try:
            if not self.s:
                self.s = socket.socket(socket.AF_INET)
                for port in range(54331, 54340):
                    try:
                        self.s.bind((get_ip.get_ip(), port))
                        break
                    except OSError:
                        pass
            else:
                self.s.close()
                self.s = socket.socket(socket.AF_INET)
            self.host = askstring('连接主机', 'ip:port').split(':')
            self.s.connect((self.host[0], int(self.host[1])))
            pwd = bytes(hashlib.new('md5', bytes(askstring('密码', '密码'), encoding='utf8')).hexdigest(), 'utf8')
            self.s.send(pwd)
            welcome = self.s.recv(1024)
            if welcome != b'welcome':
                if welcome == b'':
                    tkinter.messagebox.showerror(title='错误', message='密码错误')
                else:
                    tkinter.messagebox.showerror(title='错误', message='服务器错误')
                return
            self.menu.delete(1)
            self.menu.add_command(label=self.host[0]+':'+self.host[1], command=self.link)
            self.get_path(None, record=False)
        except IndexError:
            tkinter.messagebox.showerror(title='错误', message='格式无效')
        except ConnectionResetError:
            tkinter.messagebox.showerror(title='错误', message='密码错误')
        except ConnectionRefusedError:
            tkinter.messagebox.showerror(title='错误', message='无法连接')


if __name__ == '__main__':
    FileTransfer()
