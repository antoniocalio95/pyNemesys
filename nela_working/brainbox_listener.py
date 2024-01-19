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
import threading

from bliss.controllers.motor import Controller
from bliss.config.static import get_config


#Communication thread for brainbox serial to ethernet interface

class Brainbox_Listener(threading.Thread, Controller):

    def __init__(self, config, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        threading.Thread.__init__(self, target = self.socktopty, args = (self, ))
        self._name = "brainbox1"
        self._target = b'/dev/ttyS4'
        self._lhost = "lbm29brainbox1.esrf.fr"
        self._lport = 9001
        self._stop_event = threading.Event()

    def run(self):
        self.socktopty()
        
    def stop(self):
        self._stop_event.set()

    def is_stopped(self):
        return self._stop_event.is_set()
    
    def socktopty(self):
        
        if os.path.exists(self._target_link.decode()):
            os.unlink(self._target_link.decode())
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self._lhost, self._lport))
            master, slave = pty.openpty()
        except:
            print("Coudn't open TTY to TCP connection")

        os.symlink(str(os.ttyname(slave)),self._target_link.decode())
        print('TTY: Opened {} as {} for {}:{}'.format(os.ttyname(slave), self._target_link.decode(), self._lhost, self._lport))

        mypoll = select.poll()
        mypoll.register(s, select.POLLIN)
        mypoll.register(master, select.POLLIN)
        
        try:
            while not self.is_stopped():
                fdlist = mypoll.poll(1000)
                for fd,event in fdlist:
                    data = os.read(fd, 4096)
                    write_fd = s.fileno() if fd == master else master
                    os.write(write_fd, data)
        finally:
            if os.path.exists(self._target_link.decode()):
                os.unlink(self._target_link.decode())
            s.close()
            os.close(master)
            os.close(slave)
            print("Closing TTY to TCP connection")
            

