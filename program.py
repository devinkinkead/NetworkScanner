# Author: Devin Kinkead
import subprocess
import platform
import os
import socket
from threading import Thread
from threading import BoundedSemaphore
import datetime

validSystem = ['Windows', 'Linux']
systemType = platform.system()
results = dict()
computers = list()
threads = list()
schema = {'Local IP Address': '192.168', 'localhost': '127.0.1.1'}


# Maximum number of threads to run at once
threadLimiter = BoundedSemaphore(100)


class Ping(Thread):

    def __init__(self, device):
        super().__init__()
        self.daemon = True
        self.device = device

    def run(self):
        threadLimiter.acquire()
        self.execute_code()
        threadLimiter.release()

    def execute_code(self):
        """Pings asset, saves status (offline/online), office (if any), and ip address (if any) of the asset"""
        online = False
        average = 0
        print(f'pinging {self.device}')
        if systemType == 'Linux':
            try:
                address = socket.gethostbyname(self.device)
                param = '-c'
                command = ['ping', param, '4', address]
                # x = subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    x = subprocess.check_output(command).decode()
                except subprocess.CalledProcessError:
                    pass
                else:
                    # if x == 0:
                    # online = True

                    output_list = x.split()
                    if '100% packet loss' in x:
                        pass
                    elif 'Destination host unreachable' in x:
                        pass
                    elif 'time=' in x:
                        # print('online')
                        online = True

                        count = 0
                        # Obtain Average ping time
                        for item in output_list:
                            if item.count('/') == 3:
                                try:
                                    if count == 1:
                                        tmp_item = item.split('/')
                                        average = tmp_item[1]
                                        # print(float(average))
                                    else:
                                        count += 1
                                        continue
                                except (TypeError, ValueError) as ex:
                                    # print(ex)
                                    pass
            except socket.gaierror:
                pass

        elif systemType == 'Windows':
            try:
                address = socket.gethostbyname(self.host)
                param = '-n'
                command = ['ping', param, '4', address]
                x = str(subprocess.check_output(command))

                if 'Destination host unreachable' in x:
                    print('Offline - Unreachable')
            except socket.gaierror:
                pass
            except subprocess.CalledProcessError:
                pass
            else:
                online = True

        if online:
            office = 'Other'
            for k,v in schema.items():
                if v in address:
                    office = k
        else:
            office = 'N/A'
            address = 'N/A'
        try:
            tmp_nme = socket.gethostbyaddr(address)
            host_nme = tmp_nme[0]
        except (socket.herror, socket.gaierror, IndexError):
            host_nme = 'N/A'
        # print(host_nme)
        results[self.device] = f'{online},{office},{address},{average},{host_nme}'


if systemType not in validSystem:
    print('Program not configured for current OS. Exiting...')
    exit()

file = 'yes'
if file == 'yes':
    try:
        comp_file_name = 'computers.txt'
        with open(comp_file_name) as fp:
            for line in fp:
                temp = line.strip('\n')
                computers.append(temp)
    except FileNotFoundError:
        print(f'{comp_file_name} not in current directory. Exiting...')
else:
    for n in range(182,192):
        for m in range(1,255):
            add = f'151.101.{n}.{m}'
            computers.append(add)
# create thread for each computer
for computer in computers:
    t = Ping(computer)
    threads.append(t)


# start all the threads
for n in threads:
    n.start()
    # print(f'starting {t_count}')
    # t_count += 1

# Wait for all threads to finish
for n in threads:
    n.join()

if os.path.exists('results'):
    pass
else:
    os.mkdir('results')

d = datetime.datetime.now().timestamp()
time = datetime.datetime.fromtimestamp(d).strftime("%m-%d-%Y_%H%M")
fileName = f'Ping_results-{time}.csv'

# Saves ping results
with open(f'results/{fileName}', 'w') as fp:
    fp.write("Search-Item, Online, Office, IP Address, Avg Ping (ms), Hostname\n")
    for computer in computers:
        line = f'{computer},{results[computer]}'
        fp.write(line)
        fp.write('\n')
print(f'{fileName} saved in results folder')
