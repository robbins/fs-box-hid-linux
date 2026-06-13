import hid
import struct
from enum import IntEnum

def checksum(data, index_cs, index_remove, check, reserved):
    num = 0
    for i in range(0, len(data) - reserved):
        if i != index_remove and i != index_cs:
            num += data[i]
    num &= 0xFF
    if check:
        return data[index_cs] == num
    data[index_cs] = num
    return True

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

vid = 0x4653
pid = 0x4342

RID_INPUT = 0x01
RID_OUTPUT = 0x02
REPORT_SIZE = ((64 * 32) >> 3) + 1

with hid.Device(vid, pid) as h:
    print(f'Device manufacturer: {h.manufacturer}')
    print(f'Product: {h.product}')
    print(f'Serial Number: {h.serial}')

    read = h.read(REPORT_SIZE, timeout=2000)
    print(read.hex())
    print(read)
    print(len(read))

    payload = [0] * REPORT_SIZE
    payload[0] = RID_OUTPUT
    payload[len(payload) - 1] = 0x24

    payload[2] = CommandType.Handle_Read
    checksum(payload, 1, 1, False, 0)

    payload_out = bytes(payload)
    print(f'write: {payload_out.hex()}')
    h.write(payload_out)

    read = h.read(REPORT_SIZE, timeout=2000)
    print(f'read: {read.hex()}')
    print(len(read))
    print(f'chksum: {checksum(read, 1, 1, True, 1)}')
    if read[-2] == 35:
        print("LastWriteAck=false")
    elif read[-2] != 36:
        print("Read Invalid")
    # Remove report ID and checksum
    #for i in range(0, len(read)):
    #    if i < len(read) - 2:
    #        read[i] = read[i+2]
    #    else:
    #        read[i] = 0
    read = read[2:]
    print(f"LastWriteAck={read[-3] == 80}")
    print(read.hex())

    text = "aH4ANgZ']db0fsi<?`=%[4JOAngrY^&,rZUdlpNaJ[LD8gMVqGC=RXLyiD_IR&RBPJ_>rYyj0PJ[N=wQX_Fw[q21ly=o!hthw#Frv=7r./4U*<-&(5^*}PpoCr?W/{s@-fM{oB]B-!zJT[Ll8GP#BaXZFskj5=iH4f<89qH->ih]lzqxCzmG@|X{N)gwV7k>K-SJCN1_UiT0;njJ)p.c%PPT,01HcW@&#[n:/4j2g7Sn:Wt+KW)^8OA81g-m2tW="
    payload[2] = CommandType.Handle_Check
    payload[3] = ord(text[read[1]])
    payload[4] = ord(text[read[3]])
    payload[5] = ord(text[read[2]])
    payload[6] = ord(text[read[0]])
    checksum(payload, 1, 1, False, 0)

    payload_out = bytes(payload)
    print(f'write: {payload_out.hex()}')
    h.write(payload_out)

    read = h.read(REPORT_SIZE, timeout=2000)
    print(f'read: {read.hex()}')
    print(len(read))
    print(f'chksum: {checksum(read, 1, 1, True, 1)}')

    payload[2] = CommandType.Set_State
    payload[3] = 129
    payload[4] = 0
    payload[5] = 0
    payload[6] = 0
    payload[7] = 0
    checksum(payload, 1, 1, False, 0)

    payload_out = bytes(payload)
    print(f'write: {payload_out.hex()}')
    h.write(payload_out)

    read = h.read(REPORT_SIZE, timeout=2000)
    print(f'read: {read.hex()}')
    print(len(read))
    print(f'chksum: {checksum(read, 1, 1, True, 1)}')

    payload[2] = CommandType.Close_BLE
    payload[3] = 0
    checksum(payload, 1, 1, False, 0)

    payload_out = bytes(payload)
    print(f'write: {payload_out.hex()}')
    h.write(payload_out)

    read = h.read(REPORT_SIZE, timeout=2000)
    print(f'read: {read.hex()}')
    print(len(read))
    print(f'chksum: {checksum(read, 1, 1, True, 1)}')
