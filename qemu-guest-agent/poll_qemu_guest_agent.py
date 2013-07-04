#! /usr/bin/python

import base64
import json
import select
import socket

sock_file = "/var/lib/libvirt/qemu/test.agent"

import ipdb;ipdb.set_trace()
READ_LEN = 1024
read_file = "/proc/cpuinfo"
send_cmds = [{"execute": "guest-file-open", "arguments": {"path": read_file, "mode": "r"}},
             {"execute": "guest-file-read", "arguments": {"handle": None, "count": READ_LEN}},
             {"execute": "guest-file-close", "arguments": {"handle": None}}]

serversocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
serversocket.connect(sock_file)
serversocket.setblocking(0)

vm_fileno = serversocket.fileno()
instances = {}
instances[vm_fileno] = "instance-000004e8"

epoll = select.epoll()
epoll.register(vm_fileno, select.EPOLLIN | select.EPOLLOUT | select.EPOLLET)

try:
    #import ipdb;ipdb.set_trace()
    cmd = 0
    stop = False
    while True:
        print '-'*10 + 'start epoll' + '-'*10
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno in instances.keys():# new client is connecting
                print 'instance: ' + instances[fileno]
            if event & select.EPOLLIN:    # new msg is coming in
                print "<<<<<<<<<<<recv"
                try:
                    vm_resp = ''
                    while True:
                        vm_resp += serversocket.recv(READ_LEN)
                except socket.error:
                    pass

                epoll.modify(fileno, select.EPOLLOUT | select.EPOLLET)

                try:
                    vm_resps = vm_resp.split('\n')
                    ok_resp = None
                    for resp in vm_resps:
                        if 'error' not in resp and 'return' in resp:
                            ok_resp = resp
                            break
                        elif 'error' in resp:
                            print 'error occurs: ', resp
                    if ok_resp is not None:
                        resp = json.loads(ok_resp)
                    else:
                        print 'no valid data recv'
                        break
                except ValueError:
                    print 'response content error: ', vm_resp
                    break

                if len(send_cmds) <= cmd:
                    stop = True
                    print resp
                    break
                try:
                    if cmd == 1:
                        print('+'*10 + 'receive:' + '+'*10 + '\n' + vm_resp)
                        handle = resp["return"]
                        send_cmds[cmd]["arguments"]["handle"] = handle
                        send_cmds[cmd+1]["arguments"]["handle"] = handle
                    elif cmd == 2:
                        decoded_file = base64.decodestring(resp["return"]["buf-b64"])
                        print 'file content:\n', decoded_file
                        print resp["return"]["count"]
                        print 'EOF: ', resp["return"]["eof"]
                except (KeyError, ValueError, TypeError):
                    print 'response content error: ', resp

            elif event & select.EPOLLOUT:    # new msg need send out
                print ">>>>>>>>>send"
                if len(send_cmds) <= cmd:
                    print 'no data to send'
                    break
                try:
                    byteswritten = 0
                    data = json.dumps(send_cmds[cmd])
                    while True:
                        byteswritten += serversocket.send(data[byteswritten:])
                        if byteswritten == len(data):
                            print '*'*10 + 'send over' + '*'*10
                            break
                except socket.error:
                    pass

                epoll.modify(fileno, select.EPOLLIN | select.EPOLLET)
                cmd += 1

            elif event & select.EPOLLHUP:   # connect closed
                epoll.unregister(serversocket.fileno())
                serversocket.close()

        print '-'*10 + 'end epoll' + '-'*10 + '\n'
        if stop:
            print 'stop now'
            break
finally:
    epoll.unregister(serversocket.fileno())
    epoll.close()
    serversocket.close()

