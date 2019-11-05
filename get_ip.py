import socket
import os
import re


def get_ip():
    f = os.popen('ipconfig')
    s = f.read().replace('\n', '\\n')
    f.close()
    ip = re.search("""WLAN.+?IPv4[^:]*: ([0-9]+.[0-9]+.[0-9]+.[0-9]+)""", s).group(1)
    return ip


def get_ip_online():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.4.4', 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


if __name__ == '__main__':
    print(get_ip())
    print(get_ip_online())
