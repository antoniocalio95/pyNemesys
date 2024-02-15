# -*- coding: utf-8 -*-
#
# This file is part of the bliss project
#
# Copyright (c) 2015-2023 Beamline Control Unit, ESRF
# Distributed under the GNU LGPLv3. See LICENSE for more info.
# Author: Antonino Calio'

import os
import pty
import socket
import select
import signal

#Communication task for brainbox serial to ethernet interface

class Brainbox_Listener:
    def __init__(self):
        self._name = "brainbox1"
        self._target = "/dev/ttyS4"
        self._url = "lbm29brainbox1"
        self._port = 9001
        self._socket = None
        self._run = True

    def handler_stop_signals(self, signum, frame):
        self._run = False

    def socktopty(self):
        target_link = self._target
        if os.path.exists(target_link):
            os.unlink(target_link)

        try:
            self._socket = socket.create_connection((self._url,self._port))
            sockfd = self._socket.fileno()
            master, slave = pty.openpty()
            os.symlink(os.ttyname(slave), target_link)
            os.chmod(target_link, 0o0777)
            os.chown(target_link,1129,1664)
            print("TTY: Opened "+os.ttyname(slave)+" as "+target_link)

        except Exception as e:
            if os.path.exists(target_link):
                os.unlink(target_link)
            os.close(master)
            os.close(slave)
            self._socket.close()
            print("Couldn't open TTY to TCP connection: "+e)
            return

        poll = select.poll()

        try:
            poll.register(sockfd, select.POLLIN)
            poll.register(master, select.POLLIN)

            while self._run:
                events = poll.poll(1000)

                for fd, event in events:
                    data = os.read(fd,4096)
                    write_fd = sockfd if fd == master else master
                    os.write(write_fd,data)

        finally:
            poll.unregister(sockfd)
            poll.unregister(master)
            if os.path.exists(target_link):
                os.unlink(target_link)
            os.close(master)
            os.close(slave)
            self._socket.close()
            print("Closing TTY to TCP connection")
            

bb = Brainbox_Listener()
signal.signal(signal.SIGTERM, bb.handler_stop_signals)
bb.socktopty()
