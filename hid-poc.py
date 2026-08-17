import hid
from enum import IntEnum, auto
import sys
import hid_parser
from typing import NamedTuple
import time

class CommandType(IntEnum):
    Handle_Read = 2
    Handle_Check = 3
    Read_State = 4
    READ_DM = 5
    Read_CASE = 6
    Set_State = 7
    Set_LED_State = 8
    Power_Switch = 9
    Read_Config = 10
    Set_Config = 11
    De_Handle = 12
    Read_CV = 15
    Read_ID = 16
    IIC_Write_NByte = 32
    IIC_Read_NByte = 33
    SET_IIC_CH = 34
    SET_IIC_Rate = 35
    LED_Color_Read = 48
    LED_Color_Set = 49
    LED_COLOR_SET = 50
    Red_KCompatible = 64
    Set_KCompatible = 65
    Set_LCompatible = 66
    Set_Target_Compatible = 67
    Config_Power = 80
    Search_Power = 81
    Read_BarCode = 96
    BLESet_Read = 112
    BLESet = 113
    BLERead = 114
    Set_Board_ID = 249
    BootLoader = 250
    Reset_ME = 251
    BootloaderUpdata = 252
    Read_REV = 253
    Close_BLE = 254
    Get_Firmware = 193
    Upgrade_Firmware = 194

class BtState(IntEnum):
    ON = 1
    OFF = auto()

class Response(NamedTuple):
    last_write_ack: bool
    data: bytes

class LEDState(IntEnum):
    StatusBlinkWhite = 7

class USBHID:
    REPORT_SIZE = ((64 * 32) >> 3) + 1
    TIMEOUT_MS = 2000

    @classmethod
    def checksum(cls, data, index_cs, index_remove, check, reserved) -> bool:
        cksum = sum(data[i] for i in range(len(data) - reserved) if i != index_cs and i != index_remove)
        cksum &= 0xFF
        if check:
            return data[index_cs] == cksum
        data[index_cs] = cksum
        return True

    def __init__(self, vid, pid) -> None:
        try:
            self.device = hid.Device(vid, pid)
        except hid.HIDException:
            raise ValueError("VID/PID not found")
        rdesc = hid_parser.ReportDescriptor(self.device.get_report_descriptor()) #TODO: Was going to get size from here but the descriptor is kinda invalid or the library has a bug
        rdesc.print()
        _output_report_id = rdesc.output_report_ids[0]
        if not _output_report_id:
            raise RuntimeError("Invalid descriptor")
        self.output_report_id: int = _output_report_id

    def read(self) -> bytes | None:
        try:
            read = self.device.read(USBHID.REPORT_SIZE, USBHID.TIMEOUT_MS)
            if not read or len(read) != USBHID.REPORT_SIZE:
                return None
            if not USBHID.checksum(read, 1, 1, True, 0):
                return None
            return read[2:-1]
        except hid.HIDException:
            return None

    def write(self, data: bytes) -> bool:
        payload = bytearray(self.output_report_id.to_bytes() + data)
        if not USBHID.checksum(payload, 1, 1, False, 0):
            return False
        try:
            self.device.write(bytes(payload))
            return True
        except Exception:
            return False

    def __str__(self) -> str:
        return f"{self.device.manufacturer}:{self.device.product}:{self.device.serial}"

class FSBox:
    CHALLENGE_RESPONSE_DATA = "aH4ANgZ']db0fsi<?`=%[4JOAngrY^&,rZUdlpNaJ[LD8gMVqGC=RXLyiD_IR&RBPJ_>rYyj0PJ[N=wQX_Fw[q21ly=o!hthw#Frv=7r./4U*<-&(5^*}PpoCr?W/{s@-fM{oB]B-!zJT[Ll8GP#BaXZFskj5=iH4f<89qH->ih]lzqxCzmG@|X{N)gwV7k>K-SJCN1_UiT0;njJ)p.c%PPT,01HcW@&#[n:/4j2g7Sn:Wt+KW)^8OA81g-m2tW="

    def __init__(self, hid_transport) -> None:
        self.hid = hid_transport
        self.BtState = BtState.ON

    @classmethod
    def handle_check(cls, data: bytes) -> bytes:
        return bytes([
            ord(FSBox.CHALLENGE_RESPONSE_DATA[data[1]]),
            ord(FSBox.CHALLENGE_RESPONSE_DATA[data[3]]),
            ord(FSBox.CHALLENGE_RESPONSE_DATA[data[2]]),
            ord(FSBox.CHALLENGE_RESPONSE_DATA[data[0]]),
            ])

    def write_get_response(self, payload: bytes) -> Response | None:
        assert len(payload) == 256
        if not self.hid.write(payload):
            return None
        read = self.hid.read()
        if not read or not read[-1] == 0x24:
            return None
        return Response(last_write_ack=read[-2] == 0x50, data = read)

    @classmethod
    def build_msg(cls, cmd: CommandType, data: bytes) -> bytes:
        assert len(data) <= 253
        d = bytes([0, cmd]) + bytes(data) + bytes(253 - len(data)) + bytes([0x24])
        return d

    def ble_off(self) -> Response | None:
        r = fsbox.write_get_response(FSBox.build_msg(CommandType.Close_BLE, bytes()))
        if r.data and r.data[0] == 1:
            self.BtState = BtState.OFF
        return r

    def read_rev(self) -> str:
        r = fsbox.write_get_response(FSBox.build_msg(CommandType.Read_REV, bytes()))
        if r and not r.data:
            return ""
        return f"REV: {chr(r.data[0])}.{chr(r.data[1])}.{chr(r.data[2])}.{chr(r.data[3])}\nSID: {r.data[4:14].decode('ascii')}"

    def __str__(self) -> str:
        return str(self.hid)

if __name__ == "__main__":
    fsbox = FSBox(USBHID(0x4653, 0x4342))

    print(fsbox)
    r = fsbox.write_get_response(FSBox.build_msg(CommandType.Handle_Read, bytes()))
    r = fsbox.write_get_response(FSBox.build_msg(CommandType.Handle_Check, FSBox.handle_check(r.data)))
    r = fsbox.write_get_response(FSBox.build_msg(CommandType.Set_State, bytes([129])))
    
    # Good to send commands from this point

    print(fsbox.BtState)
    r = fsbox.ble_off()
    print(fsbox.BtState)

    print(fsbox.read_rev())
    r = fsbox.write_get_response(FSBox.build_msg(CommandType.READ_DM, bytes([1])))
    match r.data[0]:
        case 0x7:
            print("No module")
        case 0x3:
            print("SFP Detected")
        case _:
            print("?")

    r = fsbox.write_get_response(FSBox.build_msg(CommandType.Read_State, bytes()))
    if r:
        if r.data[1] == 1:
            print("RS LOS triggered")
        if r.data[2] == 1:
            print("tx fault")
