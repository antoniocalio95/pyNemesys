# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 12:28:30 2024

@author: ANTONINO16
"""

import time
import sys
from ctypes import *

# EPOS Command Library path
path = "/opt/EposCmdLib_6.3.1.0/lib/x86_64/libEposCmd.so.6.3.1.0"

# Load library
cdll.LoadLibrary(path)
epos = CDLL(path)

class Nemesys:
    
    def __init__(self, nodeID):
        
        self.nodeID = nodeID
        self.keyHandle = self.CanBusOpen()
        self.NemesysInit()
        self.ul, self.uls = self.GetConvData()
        
        
    # Open the CAN bus with the appropriate settings
    def CanBusOpen(self):
        pErrorCode = c_uint()
        deviceName = b'EPOS2'
        protocolStackName = b'MAXON_RS232'
        interfaceName = b'RS232'
        portName = b'/dev/ttyS0'
        baudrate = 115200
        timeout = 500
        keyHandle = epos.VCS_OpenDevice(deviceName, protocolStackName, interfaceName, portName, byref(pErrorCode)) # specify EPOS version and interface
        epos.VCS_SetProtocolStackSettings(keyHandle, baudrate, timeout, byref(pErrorCode)) # set baudrate and timeout
        if pErrorCode.value == 0:
            return keyHandle
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
    
    # Close CAN bus
    def CanBusClose(self):
        pErrorCode = c_uint()
        if pErrorCode.value == 0:
            return epos.VCS_CloseDevice(self.keyHandle, byref(pErrorCode)) # close device
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
    
    # Initialize pump object and enable drive
    def NemesysInit(self):
        pErrorCode = c_uint()
        epos.VCS_ClearFault(self.keyHandle, self.nodeID, byref(pErrorCode)) # clear all faults
        
        if pErrorCode.value == 0:
            return epos.VCS_SetEnableState(self.keyHandle, self.nodeID, byref(pErrorCode)) # enable device
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
    
    # Disable pump device
    def NemesysDisable(self):
        pErrorCode = c_uint()
        
        if pErrorCode.value == 0:
            return epos.VCS_SetDisableState(self.keyHandle, self.nodeID, byref(pErrorCode)) # disable device  
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
    
    # Query motor position
    def GetPositionIs(self):
        pPositionIs = c_int32()
        pErrorCode = c_uint()
        ret = epos.VCS_GetPositionIs(self.keyHandle, self.nodeID, byref(pPositionIs), byref(pErrorCode))
        
        if pErrorCode.value == 0:
            return pPositionIs.value # motor steps
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
    
    # Query motor velocity
    def GetVelocityIs(self):
        pVelocityIs = c_int32()
        pErrorCode = c_uint()
        ret = epos.VCS_GetVelocityIs(self.keyHandle, self.nodeID, byref(pVelocityIs), byref(pErrorCode))
        
        if pErrorCode.value == 0:
            return pVelocityIs.value # motor speed
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
    
    # Homing move at the positive limit switch
    def ReferencePosLim(self, wait = True):
        pErrorCode = c_uint()
        homingAcceleration = c_uint32(200000)
        speedSwitch = c_uint32(2000000)
        speedIndex = c_uint32(10000)
        homeOffset = c_int32(20000)
        currentThreshold = c_uint32(200)
        homePosition = c_int32(0)
        truePosition = self.GetPositionIs()
        epos.VCS_ActivateHomingMode(self.keyHandle, self.nodeID, byref(pErrorCode)) # activate homing mode
        epos.VCS_SetHomingParameter(self.keyHandle, self.nodeID, homingAcceleration, speedSwitch, speedIndex, homeOffset, currentThreshold, homePosition, byref(pErrorCode)) # homing settings
        epos.VCS_FindHome(self.keyHandle, self.nodeID, c_int8(18), byref(pErrorCode)) # homing motion
        if wait == True:
            while truePosition != 0:
                truePosition = self.GetPositionIs()
                print('\rPumpID: %1d Motor position: %5d ul Velocity: %5d ul/s Moving: %5s  Target Reached: %5s  Valve open: %5s' % (self.nodeID, truePosition/self.ul, self.GetVelocityIs()/self.uls, self.IsMoving(), self.TargetReached(), self.IsValveOpen()), end='', flush = True)
        
        if pErrorCode.value == 0:
            return pErrorCode
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
            
    # Homing move at the negative limit switch
    def ReferenceNegLim(self, wait = True):
        pErrorCode = c_uint()
        homingAcceleration = 200000
        speedSwitch = 2000000
        speedIndex = 10000
        homeOffset = 20000
        currentThreshold = 200
        homePosition = 0
        truePosition = self.GetPositionIs()
        epos.VCS_ActivateHomingMode(self.keyHandle, self.nodeID, byref(pErrorCode)) # activate homing mode
        epos.VCS_SetHomingParameter(self.keyHandle, self.nodeID, homingAcceleration, speedSwitch, speedIndex, homeOffset, currentThreshold, homePosition, byref(pErrorCode)) # homing settings
        epos.VCS_FindHome(self.keyHandle, self.nodeID, c_int8(17), byref(pErrorCode)) # homing motion
        if wait == True:
            while truePosition != homePosition:
                truePosition = self.GetPositionIs()
                print('\rPump ID: %1d Motor position: %5d ul Velocity: %5d ul/s Moving: %5s  Target Reached: %5s  Valve open: %5s' % (self.nodeID, truePosition/self.ul, self.GetVelocityIs()/self.uls, self.IsMoving(), self.TargetReached(), self.IsValveOpen()), end='', flush = True)
        
        if pErrorCode.value == 0:
            return pErrorCode
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
    
    # Move to position at speed
    def MoveToPositionSpeed(self, targetPosition, targetSpeed, wait = True):
        pErrorCode = c_uint()
        epos.VCS_ActivateProfilePositionMode(self.keyHandle, self.nodeID, byref(pErrorCode)) # activate profile position mode
        # Configure desired motion profile
        acceleration = 200000 # rpm/s, up to 1e7 would be possible
        deceleration = 200000 # rpm/s
        truePosition = self.GetPositionIs()
        if targetSpeed != 0:
            epos.VCS_SetPositionProfile(self.keyHandle, self.nodeID, targetSpeed*self.uls, acceleration, deceleration, byref(pErrorCode)) # set profile parameters
            epos.VCS_MoveToPosition(self.keyHandle, self.nodeID, targetPosition*self.ul, True, True, byref(pErrorCode)) # move to position
            if wait == True:
                while truePosition != targetPosition*self.ul:
                    truePosition = self.GetPositionIs()
                    print('\rPump ID: %1d Motor position: %5d ul Velocity: %5d ul/s Moving: %5s  Target Reached: %5s  Valve open: %5s' % (self.nodeID, truePosition/self.ul, self.GetVelocityIs()/self.uls, self.IsMoving(), self.TargetReached(), self.IsValveOpen()), end='', flush = True)
        elif targetSpeed == 0:
            epos.VCS_HaltPositionMovement(self.keyHandle, self.nodeID, byref(pErrorCode)) # halt motor
        
        if pErrorCode.value == 0:
            return pErrorCode
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
            
    # Halt the motor
    def Halt(self):
        pErrorCode = c_uint()
        epos.VCS_HaltPositionMovement(self.keyHandle, self.nodeID, byref(pErrorCode)) # halt motor
        epos.VCS_ClearFault(self.keyHandle, self.nodeID, byref(pErrorCode)) # clear all faults
        
        if pErrorCode.value == 0:
            return 1
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
    
    # Check if motor has reached target
    def TargetReached(self):
        pErrorCode = c_uint()
        pTargetReached = c_long()
        epos.VCS_GetMovementState(self.keyHandle, self.nodeID, byref(pTargetReached), byref(pErrorCode))
        
        if pErrorCode.value == 0:
            return bool(pTargetReached.value)
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
    
    # Check if motor is moving
    def IsMoving(self):
        pErrorCode = c_uint()
        pVelocityIs = c_long()
        epos.VCS_GetVelocityIs(self.keyHandle, self.nodeID, byref(pVelocityIs), byref(pErrorCode))
        
        if pErrorCode.value == 0:
            return bool(pVelocityIs)
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
            
    # Check if valve is open
    def IsValveOpen(self):
        pErrorCode = c_uint()
        current_state = c_ushort()
        epos.VCS_GetAllDigitalOutputs(self.keyHandle, self.nodeID, byref(current_state), byref(pErrorCode)) # Get digital output word
        
        if pErrorCode.value == 0:
            if (current_state.value & 0x1000) == 0x1000:
                return True
            else:
                return False
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
    
    # Switching of the 2-way valve connected to digital outputs C and D (bit 13 and 12, see Cetoni documentation)
    def SwitchValve(self):
        pErrorCode = c_uint()
        current_state = c_ushort()
        epos.VCS_GetAllDigitalOutputs(self.keyHandle, self.nodeID, byref(current_state), byref(pErrorCode)) # Get digital output word
        newstate = c_ushort(current_state.value ^ 0x3000) # Flip bits 12 and 13 
        epos.VCS_SetAllDigitalOutputs(self.keyHandle, self.nodeID, newstate, byref(pErrorCode)) # Send new digital output word
        time.sleep(1)
        epos.VCS_GetAllDigitalOutputs(self.keyHandle, self.nodeID, byref(current_state), byref(pErrorCode)) # Get digital output word
        newstate = c_ushort(current_state.value ^ 0x2000) # Flip bit 13
        ret = epos.VCS_SetAllDigitalOutputs(self.keyHandle, self.nodeID, newstate, byref(pErrorCode)) # Send new digital output word
        time.sleep(0.01)
        
        if pErrorCode.value == 0:
            if (newstate.value & 0x1000) == 0x1000:
                print("\nValve has been opened!")
            else:
                print("\nValve has been closed!")
            return ret  
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")
    
    # Get internal data for conversions
    def GetConvData(self):
        pErrorCode = c_uint()
        pNbOfBytesRead = c_uint()
        velexp = c_int8()
        epos.VCS_GetObject(self.keyHandle, self.nodeID, 0x608B, 0, byref(velexp), 1, byref(pNbOfBytesRead), byref(pErrorCode)) #read velocity notation exponent
        encres = c_uint32()
        epos.VCS_GetObject(self.keyHandle, self.nodeID, 0x2210, 1, byref(encres), 4, byref(pNbOfBytesRead), byref(pErrorCode)) #read encoder resolution
        gearnum = c_uint32()
        epos.VCS_GetObject(self.keyHandle, self.nodeID, 0x200C, 1, byref(gearnum), 4, byref(pNbOfBytesRead), byref(pErrorCode)) #read gear factor numerator
        geardenom = c_uint32()
        epos.VCS_GetObject(self.keyHandle, self.nodeID, 0x200C, 4, byref(geardenom), 4, byref(pNbOfBytesRead), byref(pErrorCode)) #read gear factor denominator
        qc_to_mm = int((4*encres.value) * (gearnum.value/geardenom.value))
        qc_to_ul = int(qc_to_mm / ((3.14 * (3.2574**2))/4))
        rpm_to_mms = int((60 * (gearnum.value/geardenom.value)) / (10**velexp.value))
        rpm_to_uls = int(rpm_to_mms / ((3.14 * (3.2574**2))/4))
        
        if pErrorCode.value == 0:
            return qc_to_ul, rpm_to_uls
        else:
            err_str = create_string_buffer(256)
            str_len = c_uint16(256)
            epos.VCS_GetErrorInfo(pErrorCode,byref(err_str),byref(str_len))
            print("Error Code = "+hex(pErrorCode.value)+" Error Info: "+err_str.value.decode())
            sys.exit("An Error has occurred, exiting...")


pumpA = Nemesys(2)
pumpB = Nemesys(3)

pumpA.ReferencePosLim(wait = True)
pumpB.ReferencePosLim()

pumpA.SwitchValve()
pumpA.MoveToPositionSpeed(-50, 50, wait = True)
pumpB.MoveToPositionSpeed(-50, 50)
pumpA.SwitchValve()

pumpA.ReferencePosLim(wait = True)
pumpB.ReferencePosLim()

pumpA.NemesysDisable()
pumpB.NemesysDisable()

pumpA.CanBusClose()
pumpB.CanBusClose()
