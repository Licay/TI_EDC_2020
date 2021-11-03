import sensor,image,lcd  # import 相关库
import KPU as kpu
import time
from Maix import FPIOA,GPIO#,utils
from fpioa_manager import fm
from machine import I2C
from machine import UART
import  MLX90614
import  DS_Face
import  DS_Mask
import utime
import os, sys
print(sys.path)

''''''
keyK_pin=15 # 设置按键引脚 FPIO15
keyL_pin=16 # 设置按键引脚 FPIO16
keyR_pin=17 # 设置按键引脚 FPIO17
keyT_pin=6  # 设置按键引脚 FPIO6 温度测试
light_pin=9 # 设置按键引脚 FPIO9 激光
TOF_pin=7   # 设置按键引脚 FPIO8 测距
fm.register(keyL_pin, fm.fpioa.GPIOHS1)
fm.register(keyK_pin, fm.fpioa.GPIOHS2)
fm.register(keyR_pin, fm.fpioa.GPIOHS3)
fm.register(keyT_pin, fm.fpioa.GPIOHS4)
fm.register(light_pin, fm.fpioa.GPIOHS5)
keyL = GPIO(GPIO.GPIOHS1, GPIO.IN)
keyK = GPIO(GPIO.GPIOHS2, GPIO.IN)
keyR = GPIO(GPIO.GPIOHS3, GPIO.IN)
keyT = GPIO(GPIO.GPIOHS4, GPIO.IN)
light = GPIO(GPIO.GPIOHS5, GPIO.OUT)
light.value(0)

fm.register(TOF_pin, fm.fpioa.GPIOHS6)
TOF_IO = GPIO(GPIO.GPIOHS6, GPIO.IN)

#MLX90614.TestMLX90614()
#器件iic频率只能100K~150K
i2c_MLX = I2C(I2C.I2C0, mode=I2C.MODE_MASTER, freq=100000, scl=30, sda=31, addr_size=7)
'''i2c_MLX.readfrom_mem(0x5A,  0x06, 3)
utime.sleep_ms(300)
devices = i2c_MLX.scan()
print(devices)'''

last_cm=0
last_dis=0
dis_cnt=0
def TOF_dis():
    global last_dis
    kk=0
    # Wait for GPIO pin to be asserted, but at most 6ms
    #print(TOF_IO.value())
    while TOF_IO.value() == 0:
        pass
    start = time.ticks_us()
    #print(TOF_IO.value())
    while TOF_IO.value() == 1:
        kk=time.ticks_diff(time.ticks_us(), start)
        if kk > 6000:
            break
    last_dis=last_dis*0.7+kk*0.3
    return int(last_dis/10)

TEM_CNT=0
TEM_CNT_F=0
TEM_Change=0
TEM_thread_M=37.3
TEM_thread_O=42.0
TEM_Last=37
USE_MLX=0
ItermTem=0
ManTem=0
def TemGet(mode):
    global ItermTem
    global ManTem
    if mode==0:
        return ManTem
    else:
        return ItermTem

#utils.gc_heap_size(1000000)    #修改内存堆栈大小''''''

clock = time.clock()  # 初始化系统时钟，计算帧率


fm.register(12,fm.fpioa.UART1_TX)
fm.register(13,fm.fpioa.UART1_RX)
uart_SYN = UART(UART.UART1, 9600, 8, None, 1, timeout=200, read_buf_len=10)
#uart_SYN.write('this is SYN test send\n\r')
#未知
T_weizhi=[0xCE,0xB4,0xD6,0xAA]
#成员
T_chengyuan=[0xB3,0xC9,0xD4,0xB1]
#点：
T_dian=[0xB5,0xE3]
#度：
T_du=[0xB6,0xC8]
#注意：
T_zhuyi=[0xD7,0xA2,0xD2,0xE2]
#测量温度为：
T_wendu=[0xB2,0xE2,0xC1,0xBF,0xCE,0xC2,0xB6,0xC8,0xCE,0xAA]
T_WARNING_M=[0xC4 ,0xFA ,0xB5 ,0xC4 ,0xCC ,0xE5 ,0xCE ,0xC2 ,0xB9 ,0xFD ,0xB8 ,0xDF]
T_WARNING_O=[0xB2 ,0xE2 ,0xC1 ,0xBF ,0xCE ,0xC2 ,0xB6 ,0xC8 ,0xB9 ,0xFD ,0xB8 ,0xDF]
def SYN_Send(data):
    eec=0
    buf=[0xfd,0x00,0x00,0x01,0x00]
    bufk=[0xfd,0x00,0x07,0x01,0x00,0xc4,0xe3,0xba,0xc3,0xa5]
    buf[2]=len(data)+3
    buf+=list(data)
    for i in range(len(buf)):
        eec^=int(buf[i])
    buf.append(eec)
    uart_SYN.write(bytearray(buf))
#SYN_Send(T_WARNING)
speakk=0

lcd.init() # 初始化lcd
lcd.rotation(2)
sensor.reset(freq=24000000, set_regs=True, dual_buff=True) #初始化sensor 摄像头
#sensor.reset(freq=24000000, set_regs=True) #初始化sensor
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_hmirror(1) #设置摄像头镜像
sensor.set_vflip(1)   #设置摄像头翻转
sensor.set_contrast(-1)      #对比度    +-2
sensor.set_brightness(2)    #亮度
sensor.set_saturation(-1)    #饱和度
sensor.run(1) #使能摄像头
AI_Mode=1
AI_ModeC=AI_Mode
first_in_face=0
first_in_mask=1
task_fd = kpu.load("/sd/face.smodel") # 从sd卡加载人脸检测模型
task_ld = kpu.load("/sd/five.smodel") # 从sd卡加载人脸五点关键点检测模型
task_fe = kpu.load("/sd/f196w.smodel") # 从sd卡加载人脸196维特征值模型
DS_Face.RunFirst(task_fd)

kk_MYM=1    #成员身份引入
'''
while kk_MYM<4:
    kk_MYM+=1
    img = image.Image(("/sd/image_1.jpg")%(kk_MYM)) #从SD卡文件夹中获取一张图片
    Face_date=DS_Face.RunOnce(img,task_fd,task_ld,task_fe,1)'''
'''
img = image.Image("/sd/image_1.jpg") #从SD卡文件夹中获取一张图片
a = lcd.display(img) #刷屏显示
#a = img.pix_to_ai()
Face_date=DS_Face.RunOnce(img,task_fd,task_ld,task_fe,1)'''
while True:
    Key_L=0
    Key_K=0
    Key_R=0
    Key_T=0


    #MLX_Self=MLX90614.readAmbientTempC(i2c_MLX)
    MLX_Obj=abs(MLX90614.readObjectTempC(i2c_MLX))
    #ItermTem
    #ItermTem=(0.00020557*MLX_Obj*MLX_Obj*MLX_Obj-0.02358*MLX_Obj*MLX_Obj+1.8424137*MLX_Obj-9.44855)
    ItermTem=(0.000666882*MLX_Obj*MLX_Obj*MLX_Obj-0.07084849*MLX_Obj*MLX_Obj+3.551*MLX_Obj-29.32)
    #ItermTem=MLX_Obj
    #ManTem
    ManTem=(10.5273*pow(MLX_Obj,0.35476))
    print("Man:%3.1f      Item:%3.1f\n\r"%(ManTem,ItermTem))
    #print("Self:%3.1f     Man:%3.1f      Item:%3.3f\n\r"%(MLX_Self,ManTem,ItermTem))
    ''''''

    img = sensor.snapshot() #从摄像头获取一张图片
    clock.tick() #记录时刻，用于计算帧率

    #if AI_Mode==0:  #模式选择
    if TEM_Change==0:
        if keyT.value()==0:
            if AI_Mode<3:
                Key_T=1
            else:
                TEM_CNT_F=1
            utime.sleep_ms(230)
        if keyL.value()==0:
            AI_ModeC+=1
            Key_L=1
            utime.sleep_ms(230)
        if keyR.value()==0:
            AI_ModeC-=1
            Key_R=1
            utime.sleep_ms(230)
        if keyK.value()==0:
            if (AI_Mode!=AI_ModeC) and (AI_ModeC<=2):
                if (AI_ModeC==2):
                    kpu.deinit(task_fe)
                    kpu.deinit(task_ld)
                    kpu.deinit(task_fd)
                    task_fd = kpu.load("/sd/mask.kmodel")   # 从sd卡加载口罩检测模型
                    DS_Mask.RunFirst(task_fd)
                    print('Load Mask OK')
                if (AI_ModeC==1):
                    kpu.deinit(task_fd)
                    task_fd = kpu.load("/sd/face.smodel") # 从sd卡加载人脸检测模型
                    task_ld = kpu.load("/sd/five.smodel") # 从sd卡加载人脸五点关键点检测模型
                    task_fe = kpu.load("/sd/f196w.smodel") # 从sd卡加载人脸196维特征值模型
                    DS_Face.RunFirst(task_fd)
                    print('Load Face OK')

            AI_Mode=AI_ModeC
            #Key_K=1
            utime.sleep_ms(230)
    if keyK.value()==0:
        Key_K=1
        utime.sleep_ms(230)

    if dis_cnt==30:
        dis_cnt=0
        last_cm=TOF_dis()/10
    else :
        dis_cnt+=1
    img.draw_string(0, 192, ('dis:%3.1fcm ')%(last_cm), color=(0,128,0), scale=1.5)
    img.draw_string(0, 208, ('L:%d K:%d R:%d T:%d    MAN:%3.1f   ITE:%3.1f')%(keyL.value(),keyK.value(),keyR.value(),keyT.value(),ManTem,ItermTem), color=(0,128,0), scale=1.5)
    img.draw_string(0, 224, ('ModeChoose:%d ')%(AI_ModeC), color=(0,128,0), scale=1.5)
    #utime.sleep_ms(20)

    #测温计数
    if TEM_CNT_F==1:
        TEM_CNT+=1
        if TEM_CNT==50:
            TEM_Last=TemGet(AI_Mode-3)
            light.value(0)
        if (TEM_CNT<50):
            light.value(1)
            _=img.draw_string(80,130, ("READING..."), color=(128,0,0), scale=3.5)
        if (TEM_CNT>50) and (TEM_CNT<=109):
            _=img.draw_string(80,130, ("T:%3.1fC")%(TEM_Last), color=(128,0,0), scale=3.5)
            if speakk==0:           #温度播报
                speakk=1

                T_speaker=T_wendu+list((('%3.1f')%(TEM_Last)).encode())+T_du
                if (TEM_Last>TEM_thread_M) and (AI_Mode==3):
                    T_speaker=T_speaker+T_zhuyi+T_WARNING_M
                if (TEM_Last>TEM_thread_O) and (AI_Mode==4):
                    T_speaker=T_speaker+T_zhuyi+T_WARNING_O
                SYN_Send(T_speaker)

                _=img.draw_string(80,160, ("Warnning!"), color=(128,0,0), scale=4.1)
                pass
        if TEM_CNT==110:
            speakk=0
            TEM_CNT=0
            TEM_CNT_F=0     #停止计数



    if AI_Mode==1:  #face
        Face_date=DS_Face.RunOnce(img,task_fd,task_ld,task_fe,Key_K)
        if Key_T==1:
            if Face_date[1]>80:
                SYN_Send(T_chengyuan+list((('%1d ')%(Face_date[0]+1)).encode()))
            else :
                SYN_Send(T_weizhi+T_chengyuan)

        _=img.draw_string(120,224, ("FACE"), color=(0,128,0), scale=1.5)
        pass
    if AI_Mode==2:  #mask
        DS_Mask.RunOnce(img,task_fd)
        _=img.draw_string(120,224, ("MASK"), color=(0,128,0), scale=1.5)
        pass
    if AI_Mode==3:  #MAN_TEM
        color=(0,128,0)
        if Key_K==1:
            if TEM_Change==0:
                TEM_Change=1
            else:
                TEM_Change=0
        if TEM_Change==1:
            color=(128,0,0)
            if keyL.value()==0:
                TEM_thread_M+=0.1
                utime.sleep_ms(230)
            if keyR.value()==0:
                TEM_thread_M-=0.1
                utime.sleep_ms(230)
        else:
            color=(0,128,0)

        _=img.draw_string(240, 208, ('setM:%3.1f')%(TEM_thread_M), color, scale=1.5)
        _=img.draw_string(120,224, ("MAN_TEM"), color=(0,128,0), scale=1.5)
        pass
    if AI_Mode==4:  #OBJ_TEM
        color=(0,128,0)
        if Key_K==1:
            if TEM_Change==0:
                TEM_Change=1
            else:
                TEM_Change=0
        if TEM_Change==1:
            color=(128,0,0)
            if keyL.value()==0:
                TEM_thread_O+=0.1
                utime.sleep_ms(230)
            if keyR.value()==0:
                TEM_thread_O-=0.1
                utime.sleep_ms(230)
        else:
            color=(0,128,0)

        _=img.draw_string(240, 208, ('setO:%3.1f')%(TEM_thread_O), color, scale=1.5)

        _=img.draw_string(120,224, ("OBJ_TEM"), color=(0,128,0), scale=1.5)
        pass

    fps =clock.fps() #计算帧率
    #print("%2.1f fps"%fps) #打印帧率
    #_=img.draw_string(2,2, ("%2.1ffps" %(fps)), color=(0,128,0), scale=2)
    _=img.draw_string(200,224, ("LastTem%3.1fC")%(TEM_Last), color=(0,128,0), scale=1.5)
    a = lcd.display(img) #刷屏显示

