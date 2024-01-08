import time
from ctypes import *

# EPOS Command Library path
path = './EposCmd64.dll'

# Load library
cdll.LoadLibrary(path)
epos = CDLL(path)

# Open the CAN bus with the appropriate settings
def CanBusOpen():
    pErrorCode = c_uint()
    deviceName = b'EPOS2'
    protocolStackName = b'CANopen'
    interfaceName = b'IXXAT_USB-to-CAN V2 embedded 0'
    portName = b'CAN0'
    baudrate = 1000000
    timeout = 500
    keyHandle = epos.VCS_OpenDevice(deviceName, protocolStackName, interfaceName, portName, byref(pErrorCode)) # specify EPOS version and interface
    epos.VCS_SetProtocolStackSettings(keyHandle, baudrate, timeout, byref(pErrorCode)) # set baudrate and timeout
    return keyHandle

# Close CAN bus
def CanBusClose(keyHandle):
    pErrorCode = c_uint()
    return epos.VCS_CloseDevice(keyHandle, byref(pErrorCode)) # close device

# Initialize pump object and enable drive
def NemesysInit(keyHandle, nodeID):
    pErrorCode = c_uint()
    epos.VCS_ClearFault(keyHandle, nodeID, byref(pErrorCode)) # clear all faults
    return epos.VCS_SetEnableState(keyHandle, nodeID, byref(pErrorCode)) # enable device

# Disable pump device
def NemesysDisable(keyHandle, nodeID):
    pErrorCode = c_uint()
    return epos.VCS_SetDisableState(keyHandle, nodeID, byref(pErrorCode)) # disable device  

# Query motor position
def GetPositionIs(keyHandle, nodeID):
    pPositionIs = c_long()
    pErrorCode = c_uint()
    ret = epos.VCS_GetPositionIs(keyHandle, nodeID, byref(pPositionIs), byref(pErrorCode))
    return pPositionIs.value # motor steps

# Query motor velocity
def GetVelocityIs(keyHandle, nodeID):
    pVelocityIs = c_long()
    pErrorCode = c_uint()
    ret = epos.VCS_GetVelocityIs(keyHandle, nodeID, byref(pVelocityIs), byref(pErrorCode))
    return pVelocityIs.value # motor speed

# Homing move at the positive limit switch
def ReferencePosLim(keyHandle, nodeID):
    pErrorCode = c_uint()
    homingAcceleration = 200000
    speedSwitch = 2000000
    speedIndex = 10000
    homeOffset = 20000
    currentThreshold = 200
    homePosition = 0
    truePosition = GetPositionIs(keyHandle, nodeID)
    epos.VCS_ActivateHomingMode(keyHandle, nodeID, byref(pErrorCode)) # activate homing mode
    epos.VCS_SetHomingParameter(keyHandle, nodeID, homingAcceleration, speedSwitch, speedIndex, homeOffset, currentThreshold, homePosition) # homing settings
    epos.VCS_FindHome(keyHandle, nodeID, c_int8(18), byref(pErrorCode)) # homing motion
    while truePosition != 0:
        truePosition = GetPositionIs(keyHandle, nodeID)
        print('\rMotor position: %5d ul Velocity: %5d ul/s Moving: %5s  Target Reached: %5s  Valve open: %5s' % (truePosition/ul, GetVelocityIs(keyHandle, nodeID)/uls, IsMoving(keyHandle, nodeID), TargetReached(keyHandle, nodeID), IsValveOpen(keyHandle, nodeID)), end='', flush = True)
        
# Homing move at the negative limit switch
def ReferenceNegLim(keyHandle, nodeID):
    pErrorCode = c_uint()
    homingAcceleration = 200000
    speedSwitch = 2000000
    speedIndex = 10000
    homeOffset = 20000
    currentThreshold = 200
    homePosition = 0
    truePosition = GetPositionIs(keyHandle, nodeID)
    epos.VCS_ActivateHomingMode(keyHandle, nodeID, byref(pErrorCode)) # activate homing mode
    epos.VCS_SetHomingParameter(keyHandle, nodeID, homingAcceleration, speedSwitch, speedIndex, homeOffset, currentThreshold, homePosition) # homing settings
    epos.VCS_FindHome(keyHandle, nodeID, c_int8(17), byref(pErrorCode)) # homing motion
    while truePosition != homePosition:
        truePosition = GetPositionIs(keyHandle, nodeID)
        print('\rMotor position: %5d ul Velocity: %5d ul/s Moving: %5s  Target Reached: %5s  Valve open: %5s' % (truePosition/ul, GetVelocityIs(keyHandle, nodeID)/uls, IsMoving(keyHandle, nodeID), TargetReached(keyHandle, nodeID), IsValveOpen(keyHandle, nodeID)), end='', flush = True)

# Move to position at speed
def MoveToPositionSpeed(keyHandle, nodeID, targetPosition, targetSpeed):
    pErrorCode = c_uint()
    epos.VCS_ActivateProfilePositionMode(keyHandle, nodeID, byref(pErrorCode)) # activate profile position mode
    # Configure desired motion profile
    acceleration = 200000 # rpm/s, up to 1e7 would be possible
    deceleration = 200000 # rpm/s
    truePosition = GetPositionIs(keyHandle, nodeID)
    if targetSpeed != 0:
        epos.VCS_SetPositionProfile(keyHandle, nodeID, targetSpeed, acceleration, deceleration, byref(pErrorCode)) # set profile parameters
        epos.VCS_MoveToPosition(keyHandle, nodeID, targetPosition, True, True, byref(pErrorCode)) # move to position
        while truePosition != targetPosition:
            truePosition = GetPositionIs(keyHandle, nodeID)
            print('\rMotor position: %5d ul Velocity: %5d ul/s Moving: %5s  Target Reached: %5s  Valve open: %5s' % (truePosition/ul, GetVelocityIs(keyHandle, nodeID)/uls, IsMoving(keyHandle, nodeID), TargetReached(keyHandle, nodeID), IsValveOpen(keyHandle, nodeID)), end='', flush = True)
    elif targetSpeed == 0:
        epos.VCS_HaltPositionMovement(keyHandle, nodeID, byref(pErrorCode)) # halt motor
        
# Halt the motor
def Halt(keyHandle, nodeID):
    pErrorCode = c_uint()
    epos.VCS_HaltPositionMovement(keyHandle, nodeID, byref(pErrorCode)) # halt motor
    return epos.VCS_ClearFault(keyHandle, nodeID, byref(pErrorCode)) # clear all faults

# Check if motor has reached target
def TargetReached(keyHandle, nodeID):
    pErrorCode = c_uint()
    pTargetReached = c_long()
    epos.VCS_GetMovementState(keyHandle, nodeID, byref(pTargetReached), byref(pErrorCode))
    return bool(pTargetReached.value)

# Check if motor is moving
def IsMoving(keyHandle, nodeID):
    pErrorCode = c_uint()
    pVelocityIs = c_long()
    epos.VCS_GetVelocityIs(keyHandle, nodeID, byref(pVelocityIs), byref(pErrorCode))
    return bool(pVelocityIs)
    
# Check if valve is open
def IsValveOpen(keyHandle, nodeID):
    pErrorCode = c_uint()
    current_state = c_ushort()
    epos.VCS_GetAllDigitalOutputs(keyHandle, nodeID, byref(current_state), byref(pErrorCode)) # Get digital output word
    if (current_state.value & 0x1000) == 0x1000:
        return True
    else:
        return False

# Switching of the 2-way valve connected to digital outputs C and D (bit 13 and 12, see Cetoni documentation)
def SwitchValve(keyHandle, nodeID):
    pErrorCode = c_uint()
    current_state = c_ushort()
    epos.VCS_GetAllDigitalOutputs(keyHandle, nodeID, byref(current_state), byref(pErrorCode)) # Get digital output word
    newstate = c_ushort(current_state.value ^ 0x3000) # Flip bits 12 and 13 
    epos.VCS_SetAllDigitalOutputs(keyHandle, nodeID, newstate, byref(pErrorCode)) # Send new digital output word
    time.sleep(1)
    epos.VCS_GetAllDigitalOutputs(keyHandle, nodeID, byref(current_state), byref(pErrorCode)) # Get digital output word
    newstate = c_ushort(current_state.value ^ 0x2000) # Flip bit 13
    ret = epos.VCS_SetAllDigitalOutputs(keyHandle, nodeID, newstate, byref(pErrorCode)) # Send new digital output word
    time.sleep(0.01)
    if (newstate.value & 0x1000) == 0x1000:
        print("\nValve has been opened!")
    else:
        print("\nValve has been closed!")
    return ret  

# Get internal data for conversions
def GetConvData(keyHandle, nodeID):
    pErrorCode = c_uint()
    pNbOfBytesRead = c_uint()
    velexp = c_int8()
    epos.VCS_GetObject(keyHandle, nodeID, 0x608B, 0, byref(velexp), 1, byref(pNbOfBytesRead), byref(pErrorCode)) #read velocity notation exponent
    encres = c_uint32()
    epos.VCS_GetObject(keyHandle, nodeID, 0x2210, 1, byref(encres), 4, byref(pNbOfBytesRead), byref(pErrorCode)) #read encoder resolution
    gearnum = c_uint32()
    epos.VCS_GetObject(keyHandle, nodeID, 0x200C, 1, byref(gearnum), 4, byref(pNbOfBytesRead), byref(pErrorCode)) #read gear factor numerator
    geardenom = c_uint32()
    epos.VCS_GetObject(keyHandle, nodeID, 0x200C, 4, byref(geardenom), 4, byref(pNbOfBytesRead), byref(pErrorCode)) #read gear factor denominator
    qc_to_mm = int((4*encres.value) * (gearnum.value/geardenom.value))
    qc_to_ul = int(qc_to_mm / ((3.14 * (3.2574**2))/4))
    rpm_to_mms = int((60 * (gearnum.value/geardenom.value)) / (10**velexp.value))
    rpm_to_uls = int(rpm_to_mms / ((3.14 * (3.2574**2))/4))
    return qc_to_ul, rpm_to_uls
    

if __name__ == "__main__":

    nodeID = 2
    
    keyHandle = CanBusOpen()
    NemesysInit(keyHandle, nodeID)
    ul, uls = GetConvData(keyHandle, nodeID)

    SwitchValve(keyHandle, nodeID)
    
    ReferencePosLim(keyHandle, nodeID)
    time.sleep(1)

    MoveToPositionSpeed(keyHandle, nodeID,-100*ul,20*uls) # move to position -100.000 steps at 2.000.000 mrpm/s
    time.sleep(1)
    
    ReferencePosLim(keyHandle, nodeID)
    time.sleep(1)

    SwitchValve(keyHandle, nodeID)

    NemesysDisable(keyHandle, nodeID)
    CanBusClose(keyHandle)