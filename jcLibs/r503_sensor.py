""" 
jcKarurosu
===============================================================================================
This library will provide you with some functions to be used with R503 Fingerprint
Sensor.
This library is based on the library developed by ladyada (Adafruit) on
CircuitPython, but this is intended to work in micropython. This is slightly
different and is still under development.

Adafruit Library can be founded in 
https://github.com/adafruit/Adafruit_CircuitPython_Fingerprint/blob/main/adafruit_fingerprint.py

"""
import struct
import time
from micropython import const

#Packet Parameters
_cHeaderPacket = const(0xEF01)
_cCommandPacket = const(0x1)
_cDataPacket = const(0x2)
_cAckPacket = const(0x7)
_cEndPacket = const(0x8)

#Instructions
_cGenerateImage = const(0x1)
_cGenCharFromImage = const(0x2)
_cCompare2Templates = const(0x3)
_cSearchFingerLib = const(0x4)
_cGenTemplate = const(0x5)
_cStoreTemplate = const(0x6)
_cReadTemplate = const(0x7)
_cUploadCharTemplate = const(0x8)
_cDownloadTemplate = const(0x9)
_cUploadImage = const(0xA)
_cDownloadImage = const(0xB)
_cDeleteTemplate = const(0xC)
_cEmptyFingerLib = const(0xD)
_cSetSysParam = const(0xE)
_cReadSysParam = const(0xF)
_cReadProdInfo = const(0x3C)
_cSetPassword = const(0x12)
_cVerifyPassword = const(0x13)
_cSetModuleAddress = const(0x15)
_cPortControl = const(0x17)
_cReadTemplateNum = const(0x1D)
_cReadFP_TemplateIndex = const(0x1F)
_cCancel = const(0x30)
_cAuraControl = const(0x35)
_cCheckSensor = const(0x36)
_cSoftReset = const(0x3D)

#Packet error code
Command_OK = const(0x0)
Error_ReceivingDataPackage = const(0x1)
NoFingerOnSensor = const(0x2)
ImageFail = const(0x3)
FailGenerateCharFile = const(0x6)
FailGenerateCharFile2 = const(0x7)
FingerNoMatch = const(0x8)
FailFindingMatchFinger = const(0x9)
FailCombineCharFiles = const(0xA)
PageIDBadLocation = const(0xB)
ErrorReadingTemplate = const(0xC)
ErrorUploadingTemplate = const(0xD)
ErrorCantReceiveData = const(0xE)
ErrorUploadingImage = const(0xF)
FailDeletingTemplate = const(0x10)
FailClearingFingerLib = const(0x11)
WrongPassword = const(0x13)
FailGeneratingImg = const(0x15)
ErrorWritingFlash = const(0x18)
InvalidRegisterNum = const(0x1A)
IncorrectConfigReg = const(0x1B)
FailOperatingComPort = const(0x1D)
AnError = const(0xFF)


class jc_Fingerprint:

    def __init__(self, uart):
        #Create a Fingerprint objet with UART as interface
        self.password = (0, 0, 0, 0)
        self.address = [0xFF, 0xFF, 0xFF, 0xFF]
        self.finger_ID = None
        self.confidence = None
        self.uart = uart
        self.status_register = None
        self.system_id = None
        self.library_size = None
        self.security_level = None
        self.device_addr = None
        self.data_packet_size = None
        self.baudrate = None
        self.templates = []
        self.template_count = None
        self.model = ""
        i = 0
        while True:
            if self.check_sensor() != Command_OK:
                i += 1
            else:
                break
            time.sleep(0.1)
            if i == 10:
                raise RuntimeError("Sensor return a value diferent from OK")
        i = 0
        while True:
            if self.read_SysParam() != Command_OK:
                i += 1
            else:
                break
            time.sleep(0.1)
            if i == 3:
                raise RuntimeError("There is something wrong with sensor (ReadSysParam) . . .")
        #
        print(" ---- Device Parameters ---- ")
        print("Library size -> ", end="")
        print(self.library_size)
        print("Security level -> ", end="")
        print(self.security_level)
        print("Device address -> ", end="")
        print(self.address)
        if self.read_ProdInfo() == Command_OK:
            print("Model -> ", end="")
            print(self.model)
        else:
            print(" >>>>> NO SE LEYO EL CODIGO DEL MODELO :( <<<<<<<<<<<<<<<<< )")
        print(" ---------------------------- ")
        
    def get_sensor_ans(self, len_ans, n: int = 10):
        """Read from UART a sensor answer
        len_ans = number of bytes to be read in sensor answer packet
        n = number of attempts or time to wait for a response in 100 ms steps
        returns only Confirmation_code and data if exist"""
        n_attempts = n
        ans = self.uart.read(len_ans)
        while (not ans):
            n_attempts -= 1
            if n_attempts == 0:
                return AnError
                #raise RuntimeError("Too much time to receive a response... ")
            print(" .", end="")
            time.sleep(0.1)
            ans = self.uart.read(len_ans)
            if ans:
                break
        #print("-> ans = ", end = "")    # only for debug
        #print(ans)                      # only for debug
        # Check for len of answer received and answer not empty
        if (len(ans) != len_ans):
            return AnError
            #raise RuntimeError("Failed to read data from sensor")
        # Check for right header code (bytes 0-1)
        header = struct.unpack(">H", ans[0:2])[0]
        if header != _cHeaderPacket:
            return AnError
            #raise RuntimeError("Wrong packet header")
        # Check for right Address
        addr = list(i for i in ans[2:6])
        if addr != self.address:
            return AnError
            #raise RuntimeError("Address not valid")
        # Check for ack_packet
        packet_id = ans[6]
        if packet_id != _cAckPacket:
            return AnError
            #raise RuntimeError("Not an acknowlede packet")
        packet_length = struct.unpack(">H", ans[7:9])[0]
        only_ans_data = list(i for i in ans[9 : (len(ans)-2)])
        #print("Only data ans: -> ", end="")
        #print(only_ans_data)
        # Verify the checksum
        ans_checksum = 0
        ans_checksum = packet_id + packet_length
        for element in only_ans_data:
            ans_checksum = ans_checksum + element
        if ans_checksum != struct.unpack(">H", ans[(len(ans)-2) : (len(ans))])[0]:
            return AnError
            #raise RuntimeError("Error in answer checksum")
        return only_ans_data

    def send_packet(self, data: List[int]):
        # | Header | Addr | ID | Lenght | Content | Checksum |
        # | 0xEF01 | 0xFFFFFFFF | ...
        packet = [_cHeaderPacket >> 8, _cHeaderPacket & 0xFF]
        packet = packet + self.address
        packet.append(_cCommandPacket)
        #
        p_length = len(data) + 2   #Lenght of package content (command packets and data packets) + checksum
        packet.append(p_length >> 8)
        packet.append(p_length & 0xFF)
        #
        packet = packet + data
        #
        #print("***************************")
        #print(packet)
        p_checksum = sum(packet[6:])
        packet.append(p_checksum >> 8)
        packet.append(p_checksum & 0xFF)
        #
        #print("Send_Packet: -> ", end="")
        #print(packet)
        self.uart.write(bytearray(packet))  #Sends packet in byte format through UART

    def check_sensor(self):
        self.send_packet([_cCheckSensor])   #Pasa una lista formada por un solo dato
        ans = self.get_sensor_ans(12)    #La respuesta es una cadena de 12 bytes
        if ans[0] == Command_OK:
            #print("Comunicacion con sensor establecida de forma correcta!")
            return Command_OK
        else:
            return AnError

    def read_ProdInfo(self):
        self.send_packet([_cReadProdInfo])
        sensor_ans = self.get_sensor_ans(58)
        if sensor_ans[0] != Command_OK:
            return AnError
        for c in sensor_ans[1:17]:
            self.model = self.model + chr(c)
        return sensor_ans[0]

    def read_SysParam(self):
        self.send_packet([_cReadSysParam])
        sensor_ans = self.get_sensor_ans(28)
        if sensor_ans[0] != Command_OK:
            return AnError
            #raise RuntimeError("Command 'ReadSysParam' failed . . .")
        self.status_register = struct.unpack(">H", bytes(sensor_ans[1:3]))[0]
        self.system_id = struct.unpack(">H", bytes(sensor_ans[3:5]))[0]
        self.library_size = struct.unpack(">H", bytes(sensor_ans[5:7]))[0]
        self.security_level = struct.unpack(">H", bytes(sensor_ans[7:9]))[0]
        self.device_addr = bytes(sensor_ans[9:13])
        self.data_packet_size = struct.unpack(">H", bytes(sensor_ans[13:15]))[0]
        self.baudrate = struct.unpack(">H", bytes(sensor_ans[15:17]))[0]
        return sensor_ans[0]
    
    def set_SysParam(self, n_param: int, param_val: int):
        """Set 1 of 3 system parameters 4-baudrate, 5-security_level, 6-data_packet_size
        returns 0x00 - Ok, 0x01 - Error, 0x1A - Wrong register number"""
        self.send_packet([_cSetSysParam, n_param, param_val])
        sensor_ans = self.get_sensor_ans(12)
        if sensor_ans[0] != Command_OK:
            return AnError
            #raise RuntimeError("Command 'set_SysParam' failed . . .")
        if n_param == 4:
            self.baudrate = param_val
        elif n_param == 5:
            self.security_level = param_val
        elif n_param == 6:
            self.data_packet_size = param_val
        return sensor_ans[0]


    def verify_pwd(self):
        """Send command to verify if password is correct, returns:
        0x00 - Password correct
        0x01 - Error when receiving package
        0x13 - Wrong password"""
        self.send_packet([_cVerifyPassword] + list(self.password))
        return self.get_sensor_ans(12)  #Returns only confirmation code (1 byte) for Verify Password cmd

    def count_templates(self):
        """Request the sensor to count the number of templates and stores it in
        ''self.template_count'' Returns the packet error code (0x01) or OK (0x00)"""
        self.send_packet([_cReadTemplateNum])
        sensor_ans = self.get_sensor_ans(14)
        self.template_count = int.from_bytes(sensor_ans[1:3], "big")
        return sensor_ans[0]

    def generate_image(self):
        """Requests the sensor to take an image and store it in ImageBuffer
        Returns 0x00-Ok, 0x01-Error Receiving package, 0x02-Can't detect finger, 0x03-Fail to collect finger"""
        self.send_packet([_cGenerateImage])
        return self.get_sensor_ans(12)[0]
    
    def gen_char_from_image(self, buffer_num: int=1):
        """To generate character file from the original finger image in ImageBuffer and store the file
        in CharBuffer1 or CharBuffer2
        Input parameter: BufferID
        Returns 0x00-Ok, 0x01-ErrorReceivingPackage, 0x06-Fail, 0x07-Fail, 0x15-Fail"""
        self.send_packet([_cGenCharFromImage, buffer_num])
        return self.get_sensor_ans(12)[0]

    def generate_template(self):
        """To combine information of character files from CharBuffer1 and CharBuffer2 and generate
        a template wich is stored back in both CharBuffer1 and CharBuffer2
        Returns 0x0-OK, 0x1-ErrorReceivingPackage, 0xA-Fail to combine the character files"""
        self.send_packet([_cGenTemplate])
        return self.get_sensor_ans(12)[0]

    def search_finger_lib(self):
        """Search whole finger library for the template that matches the one in CharBuffer1 or CharBuffer2
        When found, PageID will be returned
        Input parameter: BufferID (1 or 2), StartPage (searching start address), PageNum (searching numbers)
        Return: Confirmation code (1 byte), PageID (matching template location)
        Confirmation code: 0x0-Template founded, 0x1-Error, 0x9 No matching in the lib"""
        self.read_SysParam()
        capacity = self.library_size
        self.send_packet([_cSearchFingerLib, 0x01, 0x00, 0x00, capacity >> 8, capacity & 0xFF])
        sensor_ans = self.get_sensor_ans(16)
        self.finger_ID, self.confidence = struct.unpack(">HH", bytes(sensor_ans[1:5]))
        return sensor_ans[0]

    def store_template(self, PageID: int, BufferID: int = 1):
        """Store the template of specified buffer (1 or 2) at the designated location of Flash
        library. Input parameter: BufferID, PageID (2 bytes)
        Return 0x0-OK, 0x1-ErrorReceivingPackage, 0xB-Address PageID Limit Error, 0x18-Error writing Flash"""
        self.send_packet([_cStoreTemplate, BufferID, PageID >> 8, PageID & 0xFF])
        return self.get_sensor_ans(12, 10)[0]

    def delete_template(self, PageID: int):
        """Delete 1 template of Flash library started from the specified location
        or (PageID), Input Parameter: PageID (template number in Flash), N (number of templates to be deleted)
        Return 0x0-OK, 0x1-ErrorReceivingPackage, 0x10-Faile to delete templates"""
        self.send_packet([_cDeleteTemplate, PageID >> 8, PageID & 0xFF, 0x00, 0x01])
        return self.get_sensor_ans(12)[0]

    def led_ctrl(self, Ctrl_code: int, Speed: int, Color_index: int, Times: int):
        """Aura LED control, Input Parameter: Ctrl_code, Speed, ColorIndex, Times
        Ctrl_code (1 byte): 0x1-Breathing, 0x2-Flashing, 0x3-AlwaysOn, 0x4-AlwaysOff, 0x5-GraduallyOn, 0x6-GraduallyOff
        Speed (1 byte): 0x00 - 0xFF, 256 gears, minimum 5s cycle
        ColorIndex (1 byte): 1-Red, 2-Blue, 3-Purple, 4-Green, 5-Yellow, 6-Cyan, 7-White, 8-255-Off
        Times (1 byte): 0-Infinte, 1-255, only in breathing and flashing modes
        Returns 0x00-Ok, 0x01-ErrorReceivingPackage"""
        self.send_packet([_cAuraControl, Ctrl_code, Speed, Color_index, Times])
        return self.get_sensor_ans(12)[0]

    def read_templates(self):
        """Read the fingerprint template index table of the module, up to 256 at a time
        (32 bytes). Input parameter: Index page
        Returns: Confirmation code + FingerPrint template index table"""
        from math import ceil   #Round a number upward to its nearest integer:

        self.templates = []
        self.read_SysParam()
        temp_r = [0x0C, ]
        for j in range(ceil(self.library_size/256)):
            self.send_packet([_cReadFP_TemplateIndex, j])
            sensor_ans = self.get_sensor_ans(44)
            if sensor_ans[0] == Command_OK:
                for i in range(32):
                    byte = sensor_ans[i+1]
                    for bit in range(8):
                        if byte & (1 << bit):
                            self.templates.append((i*8) + bit + (j*256))
                temp_r = sensor_ans
            else:
                sensor_ans = temp_r
        return sensor_ans[0]
