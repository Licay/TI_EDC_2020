
import lcd
from machine import I2C
import utime

I2CADDR=0x5A
# RAM
RAWIR1=0x04
RAWIR2=0x05
TA=0x06
TOBJ1=0x07
TOBJ2=0x08
# EEPROM
TOMAX=0x20
TOMIN=0x21
PWMCTRL=0x22
TARANGE=0x23
EMISS=0x24
CONFIG=0x25
ADDR=0x0E
ID1=0x3C
ID2=0x3D
ID3=0x3E
ID4=0x3F

_addr=I2CADDR

def read16(i2c,reg):
    global _addr
    #global i2c0
    ret=0
    #m_data=(0,0,0)
    m_data=i2c.readfrom_mem(_addr,reg,3)
    #print(m_data)
    ret = m_data[0]
    ret |= m_data[1] << 8
    pec = m_data[2]
    return ret


def readTemp(i2c,reg):
    temp = 0.1
    temp = read16(i2c,reg)
    temp *= 0.02
    temp  -= 273.15
    return temp

def readObjectTempF(i2c):
    global TOBJ1
    return (readTemp(i2c,TOBJ1) * 9 / 5) + 32

def readAmbientTempF(i2c):
    global TA
    return (readTemp(i2c,TA) * 9 / 5) + 32

cc_tem=0
def readObjectTempC(i2c):
    global TOBJ1
    global cc_tem
    cc_tem=cc_tem*0.3+(readTemp(i2c,TOBJ1))*0.7
    return cc_tem

def readAmbientTempC(i2c):
    global TA
    return readTemp(i2c,TA)+1

def TestMLX90614():
    #器件iic频率只能100K~150K
    i2c0 = I2C(I2C.I2C0, mode=I2C.MODE_MASTER, freq=150000, scl=28, sda=29, addr_size=7)
    i2c0.readfrom_mem(0x5A,  0x06, 3)
    utime.sleep_ms(300)
    devices = i2c0.scan()
    print(devices)
    ''''''
    while True:
        MLX_Self=readAmbientTempC(i2c0)
        MLX_Obj=readObjectTempC(i2c0)
        #ItermTem
        ItermTem=0.00020557*MLX_Obj*MLX_Obj*MLX_Obj-0.02358*MLX_Obj*MLX_Obj+1.8424137*MLX_Obj-9.44855
        #ManTem
        ManTem=10.5273*pow(MLX_Obj,0.35476)
        print("Self:%3.1f     Man:%3.1f      Item:%3.3f"%(MLX_Self,ManTem,ItermTem))
        utime.sleep_ms(200)  #

if __name__ == '__main__':
    print('this is MLX90614 test')
    TestMLX90614()
else:
    print('import MLX90614')

