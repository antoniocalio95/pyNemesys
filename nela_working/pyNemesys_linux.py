# -*- coding: utf-8 -*-
#
# This file is part of the bliss project
#
# Copyright (c) 2015-2023 Beamline Control Unit, ESRF
# Distributed under the GNU LGPLv3. See LICENSE for more info.
# Author: Antonino Calio'
#
# Python wrapper for the Maxon EPOS2 command library, to control Cetoni Nemesys Low Pressure syring pumps

import time
import sys
import os
import pty
import socket
import select
import threading
from ctypes import *

# EPOS Command Library path
path = "/opt/EposCmdLib_6.3.1.0/lib/x86_64/libEposCmd.so.6.3.1.0"

# Load library
cdll.LoadLibrary(path)
epos = CDLL(path)
            
# Definition of Nemesys class
class Nemesys:
    
    # Initialization method
    def __init__(self, nodeID, port = b'/dev/ttyS4', syringe_stroke_mm = 60, syringe_diameter_mm = 3.2574):
        
        self.nodeID = nodeID
        self.port = port
        self.keyHandle = self._bus_open(self.port)
        self._nemesys_init()
        self.syr_str = syringe_stroke_mm
        self.syr_diam = syringe_diameter_mm
        self.ul, self.uls = self._get_conversion_data()
        
    # Error Handling
    def _error(self, pErrorCode):
        err_str = create_string_buffer(256)
        str_len = c_uint16(256)
        epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
        print("\nPumpID: "+str(self.nodeID)+" Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
        return 0
    
    # Open the serial bus with the appropriate settings
    def _bus_open(self, port):
        pErrorCode = c_uint()
        deviceName = b'EPOS2'
        protocolStackName = b'MAXON_RS232'
        interfaceName = b'RS232'
        portName = port
        baudrate = 115200
        timeout = 500
        try:
            keyHandle = epos.VCS_OpenDevice(deviceName, protocolStackName, interfaceName, portName, byref(pErrorCode)) # specify EPOS version and interface
            if not keyHandle:
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        try:
            if not epos.VCS_SetProtocolStackSettings(keyHandle, baudrate, timeout, byref(pErrorCode)): # set baudrate and timeout
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)

        return keyHandle
    
    # Close serial bus
    def _bus_close(self):
        pErrorCode = c_uint()
        try:
            if not epos.VCS_CloseDevice(self.keyHandle, byref(pErrorCode)): # close device
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        return pErrorCode.value
    
    # Initialize pump object and enable drive
    def _nemesys_init(self):
        pErrorCode = c_uint()
        try:
            if not epos.VCS_ClearFault(self.keyHandle, self.nodeID, byref(pErrorCode)): # clear all faults
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        try:
            if not epos.VCS_SetEnableState(self.keyHandle, self.nodeID, byref(pErrorCode)): # enable device
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        return pErrorCode.value
    
    # Disable pump device
    def _nemesys_disable(self):
        pErrorCode = c_uint()
        try:
            if not epos.VCS_SetDisableState(self.keyHandle, self.nodeID, byref(pErrorCode)): # disable device  
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        return pErrorCode.value
    
    # Query actual motor position
    def _get_position(self):
        pPositionIs = c_int32()
        pErrorCode = c_uint()
        try:
            if not epos.VCS_GetPositionIs(self.keyHandle, self.nodeID, byref(pPositionIs), byref(pErrorCode)):
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        return pPositionIs.value # motor steps
    
    # Query actual motor velocity
    def _get_velocity(self):
        pVelocityIs = c_int32()
        pErrorCode = c_uint()
        try:
            if not epos.VCS_GetVelocityIs(self.keyHandle, self.nodeID, byref(pVelocityIs), byref(pErrorCode)):
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        return pVelocityIs.value # motor speed
    
    # Homing move at the positive limit switch
    def _reference_pos_lim(self, wait = True):
        pErrorCode = c_uint()
        homingAcceleration = c_uint32(200000)
        speedSwitch = c_uint32(2000000)
        speedIndex = c_uint32(10000)
        homeOffset = c_int32(20000)
        currentThreshold = c_uint32(200)
        homePosition = c_int32(0)
        truePosition = self._get_position()
        try:
            if not epos.VCS_ActivateHomingMode(self.keyHandle, self.nodeID, byref(pErrorCode)): # activate homing mode
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        try:
            if not epos.VCS_SetHomingParameter(self.keyHandle, self.nodeID, homingAcceleration, speedSwitch, speedIndex, homeOffset, currentThreshold, homePosition, byref(pErrorCode)): # homing settings
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        try:
            if not epos.VCS_FindHome(self.keyHandle, self.nodeID, c_int8(18), byref(pErrorCode)): # homing motion
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        if wait == True:
            while truePosition != 0:
                truePosition = self._get_position()
                print('\rPumpID: %1d Motor position: %5d ul Velocity: %5d ul/s Moving: %5s  Target Reached: %5s  Valve open: %5s' % (self.nodeID, truePosition/self.ul, self._get_velocity()/self.uls, self._is_moving(), self._is_target_reached(), self._is_valve_open()), end='', flush = True)
        return pErrorCode.value
            
    # Homing move at the negative limit switch
    def _reference_neg_lim(self, wait = True):
        pErrorCode = c_uint()
        homingAcceleration = 200000
        speedSwitch = 2000000
        speedIndex = 10000
        homeOffset = 20000
        currentThreshold = 200
        homePosition = 0
        truePosition = self._get_position()
        try:
            if not epos.VCS_ActivateHomingMode(self.keyHandle, self.nodeID, byref(pErrorCode)): # activate homing mode
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        try:
            if not epos.VCS_SetHomingParameter(self.keyHandle, self.nodeID, homingAcceleration, speedSwitch, speedIndex, homeOffset, currentThreshold, homePosition, byref(pErrorCode)): # homing settings
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        try:
            if not epos.VCS_FindHome(self.keyHandle, self.nodeID, c_int8(17), byref(pErrorCode)): # homing motion
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        if wait == True:
            while truePosition != homePosition:
                truePosition = self._get_position()
                print('\rPump ID: %1d Motor position: %5d ul Velocity: %5d ul/s Moving: %5s  Target Reached: %5s  Valve open: %5s' % (self.nodeID, truePosition/self.ul, self._get_velocity()/self.uls, self._is_moving(), self._is_target_reached(), self._is_valve_open()), end='', flush = True)
        return pErrorCode.value
    
    # Move to position at speed
    def _move_to_position_speed(self, targetPosition, targetSpeed, wait = True):
        pErrorCode = c_uint()
        try:
            if not epos.VCS_ActivateProfilePositionMode(self.keyHandle, self.nodeID, byref(pErrorCode)): # activate profile position mode
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        # Configure desired motion profile
        acceleration = 200000 # rpm/s, up to 1e7 would be possible
        deceleration = 200000 # rpm/s
        truePosition = self._get_position()
        if targetSpeed != 0:
            try:
                if not epos.VCS_SetPositionProfile(self.keyHandle, self.nodeID, targetSpeed*self.uls, acceleration, deceleration, byref(pErrorCode)): # set profile parameters
                    raise Exception("An Error has occurred, exiting...")
            except:
                self._error(pErrorCode)
            try:
                if not epos.VCS_MoveToPosition(self.keyHandle, self.nodeID, c_int32(targetPosition*self.ul), True, True, byref(pErrorCode)): # move to position
                    raise Exception("An Error has occurred, exiting...")
            except:
                self._error(pErrorCode)
            if wait == True:
                while truePosition != targetPosition*self.ul:
                    truePosition = self._get_position()
                    print('\rPump ID: %1d Motor position: %5d ul Velocity: %5d ul/s Moving: %5s  Target Reached: %5s  Valve open: %5s' % (self.nodeID, truePosition/self.ul, self._get_velocity()/self.uls, self._is_moving(), self._is_target_reached(), self._is_valve_open()), end='', flush = True)
        elif targetSpeed == 0:
            try:
                if not epos.VCS_HaltPositionMovement(self.keyHandle, self.nodeID, byref(pErrorCode)): # halt motor
                    raise Exception("An Error has occurred, exiting...")
            except:
                self._error(pErrorCode)
        return pErrorCode.value
            
    # Set speed but doesn't move
    def _set_speed(self, targetSpeed):
        pErrorCode = c_uint()
        try:
            if not epos.VCS_ActivateProfilePositionMode(self.keyHandle, self.nodeID, byref(pErrorCode)): # activate profile position mode
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        # Configure desired motion profile
        acceleration = 200000 # rpm/s, up to 1e7 would be possible
        deceleration = 200000 # rpm/s
        pVelocity = c_uint32()
        pAcc = c_uint32()
        pDec = c_uint32()
        if targetSpeed != 0:
            try:
                if not epos.VCS_SetPositionProfile(self.keyHandle, self.nodeID, targetSpeed*self.uls, acceleration, deceleration, byref(pErrorCode)): # set profile parameters
                    raise Exception("An Error has occurred, exiting...")
            except:
                self._error(pErrorCode)
            try:
                if not epos.VCS_GetPositionProfile(self.keyHandle, self.nodeID, byref(pVelocity), byref(pAcc), byref(pDec), byref(pErrorCode)): # get profile parameters
                    raise Exception("An Error has occurred, exiting...")
            except:
                self._error(pErrorCode)
            print('\nPump ID: %1d New set velocity value: %5d ul/s \n' % (self.nodeID, pVelocity.value/self.uls))
        elif targetSpeed == 0:
            try:
                if not epos.VCS_HaltPositionMovement(self.keyHandle, self.nodeID, byref(pErrorCode)): # halt motor
                    raise Exception("An Error has occurred, exiting...")
            except:
                self._error(pErrorCode)
            print("Speed cannot be 0!")
        return pErrorCode.value
            
    # Get set speed (not instantaneous)
    def _get_set_speed(self):
        pErrorCode = c_uint()
        pVelocity = c_uint32()
        pAcc = c_uint32()
        pDec = c_uint32()
        pMode = c_int8()
        try:
            if not epos.VCS_GetOperationMode(self.keyHandle, self.nodeID, byref(pMode), byref(pErrorCode)): # Check if device is in profile position mode
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        if pMode.value == 1:
            try:
                if not epos.VCS_GetPositionProfile(self.keyHandle, self.nodeID, byref(pVelocity), byref(pAcc), byref(pDec), byref(pErrorCode)): # get profile parameters
                    raise Exception("An Error has occurred, exiting...")
            except:
                self._error(pErrorCode)
            print('\nPump ID: %1d Set velocity value: %5d ul/s \n' % (self.nodeID, pVelocity.value/self.uls))
            return pVelocity.value/self.uls
        else:
            print("\n!! You have to set the speed first !!\n")
            return pErrorCode.value
            
    # Move to position with set speed
    def _move_at_set_speed(self, targetPosition, wait = True):
        pErrorCode = c_uint()
        pMode = c_int8()
        try:
            if not epos.VCS_GetOperationMode(self.keyHandle, self.nodeID, byref(pMode), byref(pErrorCode)): # Check if device is in profile position mode
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        truePosition = self._get_position()
        if pMode.value == 1:
            try:
                if not epos.VCS_MoveToPosition(self.keyHandle, self.nodeID, targetPosition*self.ul, True, True, byref(pErrorCode)): # move to position
                    raise Exception("An Error has occurred, exiting...")
            except:
                self._error(pErrorCode)
            if wait == True:
                while truePosition != targetPosition*self.ul:
                    truePosition = self._get_position()
                    print('\rPump ID: %1d Motor position: %5d ul Velocity: %5d ul/s Moving: %5s  Target Reached: %5s  Valve open: %5s' % (self.nodeID, truePosition/self.ul, self._get_velocity()/self.uls, self._is_moving(), self._is_target_reached(), self._is_valve_open()), end='', flush = True)
        else:
            print("\n!! You have to set the speed first !!\n")
        return pErrorCode.value
            
    # Halt the motor
    def _halt(self):
        pErrorCode = c_uint()
        try:
            if not epos.VCS_HaltPositionMovement(self.keyHandle, self.nodeID, byref(pErrorCode)): # halt motor
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        try:
            if notepos.VCS_ClearFault(self.keyHandle, self.nodeID, byref(pErrorCode)): # clear all faults
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        return pErrorCode.value
    
    # Check if motor has reached target
    def _is_target_reached(self):
        pErrorCode = c_uint()
        pTargetReached = c_long()
        try:
            if not epos.VCS_GetMovementState(self.keyHandle, self.nodeID, byref(pTargetReached), byref(pErrorCode)):
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        return bool(pTargetReached.value)
    
    # Check if motor is moving
    def _is_moving(self):
        pErrorCode = c_uint()
        pVelocityIs = c_long()
        try:
            if not epos.VCS_GetVelocityIs(self.keyHandle, self.nodeID, byref(pVelocityIs), byref(pErrorCode)):
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        return bool(pVelocityIs)
    
    # Check if valve is open
    def _is_valve_open(self):
        pErrorCode = c_uint()
        current_state = c_ushort()
        try:
            if not epos.VCS_GetAllDigitalOutputs(self.keyHandle, self.nodeID, byref(current_state), byref(pErrorCode)): # Get digital output word
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        if (current_state.value & 0x1000) == 0x1000:
            return True
        else:
            return False
    
    # Switching of the 2-way valve connected to digital outputs C and D (bit 13 and 12, see Cetoni documentation)
    def _switch_valve(self):
        pErrorCode = c_uint()
        current_state = c_ushort()
        try:
            if not epos.VCS_GetAllDigitalOutputs(self.keyHandle, self.nodeID, byref(current_state), byref(pErrorCode)): # Get digital output word
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        newstate = c_ushort(current_state.value ^ 0x3000) # Flip bits 12 and 13 
        try:
            if not epos.VCS_SetAllDigitalOutputs(self.keyHandle, self.nodeID, newstate, byref(pErrorCode)): # Send new digital output word
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        time.sleep(0.2)
        try:
            if not epos.VCS_GetAllDigitalOutputs(self.keyHandle, self.nodeID, byref(current_state), byref(pErrorCode)): # Get digital output word
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        newstate = c_ushort(current_state.value ^ 0x2000) # Flip bit 13
        try:
            if not epos.VCS_SetAllDigitalOutputs(self.keyHandle, self.nodeID, newstate, byref(pErrorCode)): # Send new digital output word
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        time.sleep(0.01)
        if (newstate.value & 0x1000) == 0x1000:
            print("\nPump ID: %1d Valve has been opened!" %self.nodeID)
        else:
            print("\nPump ID: %1d Valve has been closed!" %self.nodeID)
        return pErrorCode.value
    
    # Get internal data for conversions
    def _get_conversion_data(self):
        pErrorCode = c_uint()
        pNbOfBytesRead = c_uint()
        velexp = c_int8()
        try:
            if not epos.VCS_GetObject(self.keyHandle, self.nodeID, 0x608B, 0, byref(velexp), 1, byref(pNbOfBytesRead), byref(pErrorCode)): #read velocity notation exponent
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        encres = c_uint32()
        try:
            if not epos.VCS_GetObject(self.keyHandle, self.nodeID, 0x2210, 1, byref(encres), 4, byref(pNbOfBytesRead), byref(pErrorCode)): #read encoder resolution
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        gearnum = c_uint32()
        try:
            if not epos.VCS_GetObject(self.keyHandle, self.nodeID, 0x200C, 1, byref(gearnum), 4, byref(pNbOfBytesRead), byref(pErrorCode)): #read gear factor numerator
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        geardenom = c_uint32()
        try:
            if not epos.VCS_GetObject(self.keyHandle, self.nodeID, 0x200C, 4, byref(geardenom), 4, byref(pNbOfBytesRead), byref(pErrorCode)): #read gear factor denominator
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        try:
            qc_to_mm = int((4*encres.value) * (gearnum.value/geardenom.value))
            qc_to_ul = int(qc_to_mm / ((3.14 * (self.syr_diam**2))/4))
            rpm_to_mms = int((self.syr_str * (gearnum.value/geardenom.value)) / (10**velexp.value))
            rpm_to_uls = int(rpm_to_mms / ((3.14 * (self.syr_diam**2))/4))
        except:
            self._error(pErrorCode)
            qc_to_ul = 1
            rpm_to_uls = 1
        return qc_to_ul, rpm_to_uls

    def _print_info(self):
        print('\nPumpID: %1d Motor position: %5d ul Velocity: %5d ul/s Moving: %5s  Target Reached: %5s  Valve open: %5s\n' % (self.nodeID, self._get_position()/self.ul, self._get_velocity()/self.uls, self._is_moving(), self._is_target_reached(), self._is_valve_open()), end='', flush = True)
        return 0
    
    def _pump_state(self):
        pErrorCode = c_uint()
        pMode = c_int8()
        try:
            if not epos.VCS_GetOperationMode(self.keyHandle, self.nodeID, byref(pMode), byref(pErrorCode)): # Check if device is in profile position mode
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)
        if pMode.value == 1:
            print("Pump %d is in Profile Position Mode, the set speed is %5d ul/s" % (self.nodeID, self._get_set_speed()))
        elif pMode.value == 6:
            print("Pump %d is in Homing Mode" % self.nodeID)
        else:
            print("Pump %d is not in Homing or Profile Position Mode, please re-initialize it!" % self.nodeID)
        self._print_info()
        return pErrorCode.value

    def _get_state(self):
        pErrorCode = c_uint()
        pState = c_uint16()
        try:
            if not epos.VCS_GetState(self.keyHandle, self.nodeID, byref(pState), byref (pErrorCode)):
                raise Exception("An Error has occurred, exiting...")
        except:
            self._error(pErrorCode)

        if pState.value == 0:
            print("Pump %1d state: DISABLED" %self.nodeID)
            return "DISABLED"
        if pState.value == 1:
            print("Pump %1d state: ENABLED" %self.nodeID)
            return "ENABLED"
        if pState.value == 2:
            print("Pump %1d state: QUICKSTOP" %self.nodeID)
            return "QUICKSTOP"
        if pState.value == 3:
            print("Pump %1d state: FAULT" %self.nodeID)
            return "FAULT"
        
"""
Test code

pumpA = Nemesys(2)
pumpB = Nemesys(3)

pumpA._reference_pos_lim(wait = False)
pumpB._reference_pos_lim()

pumpA._switch_valve()
pumpB._switch_valve()

pumpA._move_to_position_speed(-50, 50, wait = False)
pumpB._move_to_position_speed(-50, 50)

pumpA._switch_valve()
pumpB._switch_valve()

pumpA._reference_pos_lim(wait = False)
pumpB._reference_pos_lim()

pumpA._nemesys_disable()
pumpB._nemesys_disable()

pumpA._bus_close()
pumpB._bus_close()
"""
