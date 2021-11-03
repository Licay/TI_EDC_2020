import sensor, image, lcd, time
import KPU as kpu

color_R = (255, 0, 0)
color_G = (0, 255, 0)
color_B = (0, 0, 255)

class_IDs = ['no_mask', 'mask']

anchor = (0.1606, 0.3562, 0.4712, 0.9568, 0.9877, 1.9108, 1.8761, 3.5310, 3.4423, 5.6823)


def drawConfidenceText(img, rol, classid, value):
    text = ""
    _confidence = int(value * 100)

    if classid == 1:
        text = 'mask: ' + str(_confidence) + '%'
    else:
        text = 'no_mask: ' + str(_confidence) + '%'

    img.draw_string(rol[0], rol[1], text, color=color_R, scale=1.5)


def BasicInit():
    lcd.init()
    sensor.reset(dual_buff=True)
    #sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.set_hmirror(0)
    sensor.run(1)


def RunFirst(task):
    _ = kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)



def RunOnce(img,task):
    code = kpu.run_yolo2(task, img)
    if code:
        totalRes = len(code)

        for item in code:
            confidence = float(item.value())
            itemROL = item.rect()
            classID = int(item.classid())
            '''
            if confidence < 0.52:
                _ = img.draw_rectangle(itemROL, color=color_B, tickness=5)
                continue
            '''

            if classID == 1 and confidence > 0.65:
                _ = img.draw_rectangle(itemROL, color_G, tickness=5)
                if totalRes == 1:
                    drawConfidenceText(img, (item.x(), item.y()), 1, confidence)
            else:
                _ = img.draw_rectangle(itemROL, color=color_R, tickness=5)
                if totalRes == 1:
                    drawConfidenceText(img, (item.x(), item.y()), 0, confidence)






def TestDS_Mask():
    task = kpu.load("/sd/mask.kmodel")
    #task = kpu.load_flash(0x600000, 0, 0, 60000000)
    RunFirst(task)
    BasicInit()
    clock = time.clock()
    img_lcd = image.Image()
    while True:
        img = sensor.snapshot()
        clock.tick()
        RunOnce(img,task)
        print(clock.fps())
        _ = lcd.display(img)
    _ = kpu.deinit(img,task)


if __name__ == '__main__':
    print('this is DS_Mask test')
    TestDS_Mask()
else:
    print('import DS_Mask')
