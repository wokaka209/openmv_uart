import sensor,image, time,math
from pyb import UART

sensor.reset()                      # 重置感光元件，重置摄像机
sensor.set_pixformat(sensor.RGB565) # 设置颜色格式为RGB565，彩色，每个像素16bit。
sensor.set_framesize(sensor.QVGA)  # 图像大小为QVGA，大小320*240
sensor.skip_frames(time = 2000)     #延时跳过一些帧，等待感光元件变稳定
sensor.set_auto_gain(False)          #黑线不易识别时，将此处写False
sensor.set_auto_whitebal(False)     #颜色识别必须关闭白平衡，会影响颜色识别效果，导致颜色的阈值发生改变
sensor.set_auto_exposure(False)
clock = time.clock()                # 创建一个时钟对象来跟踪FPS。
uart = UART(3, 9600)

#sensor.set_auto_exposure(True, exposure_us=5000) # 设置自动曝光sensor.get_exposure_us()
img=0

# 调试变量和对应的标志位
i=0
color_flag=0
mode_flag=0
burry=0
adj_yz=0
color_box=[]
yes_flag=0

# 串口发送变量，每个模式发一次
long_t_flag=0
s_t_flag=0
color_blob_flag=0
result_1=0
result_2=0
result_3=0
qr_flag=0

#图像大小为QVGA，大小320*240
#roi的格式是(x, y, w, h)
track_roi= [(89,120,8,8),
            (97,120,8,8),
           (105,120,8,8),
           (113,120,8,8),
           (121,120,8,8),
           (129,120,8,8),
           (137,120,8,8),
           (145,120,8,8),
           (153,120,8,8),
           (161,120,8,8),
           (169,120,8,8),
           (177,120,8,8),
           (185,120,8,8),
           (193,120,8,8),
           (201,120,8,8),
           (209,120,8,8)]


# 红色阈值1
pink_threshold =(0, 51, 15, 127, -128, 127)
# 黄色阈值2
yellow_threshold = (38, 100, -12, 0, 14, 126)
# 蓝色阈值4
blue_threshold = (0, 55, -7, 9, -31, -11)
# 绿色阈值8
green_threshold =(24, 49, -34, -10, -128, 127)
# 色块roi
blob_roi=(79,24,168,201)

thresholds = (0, 7, -13, -1, -22, 4)#黑色的颜色阈值#黑色的颜色阈值
#识别形状和颜色
max_blob=0
row_data=[-1,-1]


# 串口储存数组
box_1=[]    #长短线
box_2=[]    #二维码
box_3=[]    #色块
#________________________________________________________________
# 统计我的视觉格子有多少个1
def count_ones_in_hex(hex_num):
    binary_num = bin(int(hex_num, 16))[2:]
    count_ones = binary_num.count('1')
    return count_ones


#长短线相关变量
count_one=0
hex_16bit=0


# 结构体
class target_check(object):
    x=0          #int16_t,横线上被标记黑点的地方，从左到右依次减少

target=target_check()


# 绘制水平线
def draw_hori_line(img, x0, x1, y, color):
    for x in range(x0, x1):
        img.set_pixel(x, y, color)
# 绘制竖直线
def draw_vec_line(img, x, y0, y1, color):
    for y in range(y0, y1):
        img.set_pixel(x, y, color)
# 绘制矩形
def draw_rect(img, x, y, w, h, color):
    draw_hori_line(img, x, x+w, y, color)
    draw_hori_line(img, x, x+w, y+h, color)
    draw_vec_line(img, x, y, y+h, color)
    draw_vec_line(img, x+w, y, y+h, color)


hor_bits=['0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0'] #记录横线16个感兴趣区是否为黑线
#__________________________________________________________________
def findtrack():
    global img,target,box_1
    target.x=0
    #用于检测黑线
    for i in range(0,16):
        hor_bits[i]=0
        '''
        thresholds表示黑色线阈值，roi为感兴趣区
        merge=True，表示所有合并所有重叠的blob为一个
        margin 边界，如果设置为10，那么两个blobs如果间距10一个像素点，也会被合并。
        '''
        blobs=img.find_blobs([thresholds],roi=track_roi[i],margin=50,merge=True)
        #如果识别到了黑线，hor_bits对应位置1
        for b in blobs:
            hor_bits[i]=1


    #绘制16个横线红色四个角
    for k in range(0,16):
        if  hor_bits[k]:
            target.x=target.x|(0x01<<(15-k))
            img.draw_circle(int(track_roi[k][0]+track_roi[k][2]*0.5),int(track_roi[k][1]+track_roi[k][3]*0.5),1,(255,0,0))
    #绘制16个横线感兴趣区
    for rec in track_roi:
        img.draw_rectangle(rec, color=(0,255,0))#绘制出roi区域
    hex_16bit=hex(target.x)
    count_one = count_ones_in_hex(hex_16bit)
    if count_one >= 7 and count_one <=10:
        box_1.append(10)
    elif count_one >= 5 and count_one <=6:
        box_1.append(11)

# blobs打包的数据
def package_blobs_data():
    return bytearray([target.x >> 8,
                      target.x
                      ])
#__________________________________________________________________
def QR_find_code():

    img = sensor.snapshot()
    for code in img.find_qrcodes(roi=blob_roi):
        if code.payload() == "0":
            box_2.append(0)
        elif code.payload() == "1":
            box_2.append(1)
        elif code.payload() == "2":
            box_2.append(2)
        elif code.payload() == "3":
            box_2.append(3)
        elif code.payload() == "4":
            box_2.append(4)
        elif code.payload() == "5":
            box_2.append(5)
        elif code.payload() == "6":
            box_2.append(6)
        elif code.payload() == "7":
            box_2.append(7)
        elif code.payload() == "8":
            box_2.append(8)
        elif code.payload() == "9":
            box_2.append(9)
#___________________________________________________________________
def most_common_number(numbers):
    count_dict = {}
    for num in numbers:
        count_dict[num] = count_dict.get(num, 0) + 1
    max_count = max(count_dict.values())
    most_common_numbers = [num for num, count in count_dict.items() if count == max_count]
    return most_common_numbers
#_________________________________________________________
def detect():#输入的是寻找到色块中的最大色块
    global img
    row_data=[-1,-1]#保存颜色和形状
    max_blobs=img.find_blobs([pink_threshold, yellow_threshold , blue_threshold , green_threshold], area_threshold=1000,roi=blob_roi)
    for max_blob in max_blobs:

        if max_blob.density()>0.6:
            row_data[0]=max_blob.code()
            row_data[1]=3#表示圆
        elif max_blob.density()>0.4:
            row_data[0]=max_blob.code()
            row_data[1]=4#表示三角形
    if row_data[0] == 8 and row_data[1] == 3:
        box_3.append(12)
    elif row_data[0]==1 and row_data[1]==3:
        box_3.append(13)
    elif row_data[0]==1 and row_data[1]==4:
        box_3.append(14)
    elif row_data[0]==4 and row_data[1]==3:
        box_3.append(15)
    elif row_data[0]==2 and row_data[1]==4:
        box_3.append(16)

#________________________________________________
def uart_function():
    global uart,burry,mode_flag,color_flag,adj_yz,i,yes_flag
    if uart.any():
        burry=uart.read().decode()
        if burry == "0":
            burry=0
            mode_flag+=1
            if mode_flag>1:
                mode_flag=0
        elif burry == "1":
            burry=0
            color_flag +=1
            if color_flag >4:
                color_flag=0
        elif burry == "2":
            burry=0
            adj_yz=1
        elif burry == "3":
            burry=0
            adj_yz=2
        elif burry == "4":
            burry=0
            i+=1
            if i>5:
                i=0
        elif burry == "5":
            burry=0
            yes_flag=1
        elif burry == "11":
            burry=0
            mode_flag=11
        elif burry == "12":
            burry=0
            mode_flag=12
        elif burry == "13":
            burry=0
            mode_flag=13
        elif burry == "14":
            burry=0
            mode_flag=14
        elif burry == "15":
            burry=0
            mode_flag=15
        elif burry == "16":
            burry=0
            mode_flag=16



#________________________________________________
while True:
    img=sensor.snapshot()
    uart_function()
    if mode_flag==0:
        if color_flag==0:
            while color_flag == 0:
                if mmode_flag!=0:
                    break
                img=sensor.snapshot().binary([color_box])
                color_box=pink_threshold
                if adj_yz==1:
                    color_box[i]=pink_threshold[i] + 1
                elif adj_yz==2:
                    color_box[i]=pink_threshold[i] - 1
                if yes_flag == 1:
                    pink_threshold=color_box
                    yes_flag=0


        elif colo_flag==1:
            while color_flag == 1:
                if mode_flag!=0:
                    break
                img=sensor.snapshot().binary([color_box])
                color_box=yellow_threshold
                if adj_yz==1:
                    color_box[i]=yellow_threshold[i] + 1
                elif adj_yz==2:
                    color_box[i]=yellow_threshold[i] - 1
                if yes_flag == 1:
                    yellow_threshold=color_box
                    yes_flag=0


        elif colo_flag == 2:
            while color_flag == 2:
                if mode_flag!=0:
                    break
                img=sensor.snapshot().binary([color_box])
                color_box=blue_threshold
                if adj_yz==1:
                    color_box[i]=blue_threshold[i] + 1
                elif adj_yz==2:
                    color_box[i]=blue_threshold[i] - 1
                if yes_flag == 1:
                    blue_threshold=color_box
                    yes_flag=0



        elif colo_flag == 3:
            while color_flag == 3:
                if mode_flag!=0:
                    break
                img=sensor.snapshot().binary([color_box])
                color_box=green_threshold
                if adj_yz==1:
                    color_box[i]=green_threshold[i] + 1
                elif adj_yz==2:
                    color_box[i]=green_threshold[i] - 1
                if yes_flag == 1:
                    green_threshold=color_box
                    yes_flag=0


        elif colo_flag == 4:
            while color_flag == 4:
                if mode_flag!=0:
                    break
                img=sensor.snapshot().binary([color_box])
                color_box=thresholds
                if adj_yz==1:
                    color_box[i]=thresholds[i] + 1
                elif adj_yz==2:
                    color_box[i]=thresholds[i] - 1
                if yes_flag == 1:
                    thresholds=color_box
                    yes_flag=0
    elif mode_flag == 1:#mode1
        findtrack() # 长短线服务函数
        detect()   # 色块
        QR_find_code() #二维码

        if len(box_1)==100:
            result_1 = most_common_number(box_1)
            if result_1 == 10:
                uart.write(result_1)
                box_1.clear()
                result_1=0
            elif result_1 == 11:
                uart.write(result_1)
                box_1.clear()
                result_1=0


        elif len(box_3)==100:
            result_3 = most_common_number(box_3)
            if result_3 == 12:
                uart.write(result_3)
                box_3.clear()
                result_3=0
            elif result_3 == 13:
                uart.write(result_3)
                box_3.clear()
                result_3=0
            elif result_3 == 14:
                uart.write(result_3)
                box_3.clear()
                result_3=0
            elif result_3 == 15:
                uart.write(result_3)
                box_3.clear()
                result_3=0
            elif result_3 == 16:
                uart.write(result_3)
                box_3.clear()
                result_3=0

        elif  len(box_2)==100:
            result_2 = most_common_number(box_2)
            if result_2 == 0:
                uart.write(result_2)
                box_2.clear()
                result_2=0
            elif result_2 == 1:
                uart.write(result_2)
                box_2.clear()
                result_2=0
            elif result_2 == 2:
                uart.write(result_2)
                box_2.clear()
                result_2=0
            elif result_2 == 3:
                uart.write(result_2)
                box_2.clear()
                result_2=0
            elif result_2 == 4:
                uart.write(result_2)
                box_2.clear()
                result_2=0
            elif result_2 == 5:
                uart.write(result_2)
                box_2.clear()
                result_2=0
            elif result_2 == 6:
                uart.write(result_2)
                box_2.clear()
                result_2=0
            elif result_2 == 7:
                uart.write(result_2)
                box_2.clear()
                result_2=0
            elif result_2 == 8:
                uart.write(result_2)
                box_2.clear()
                result_2=0
            elif result_2 == 9:
                uart.write(result_2)
                box_2.clear()
                result_2=0
    elif mode_flag==10:

        mode_flag==1










    #print(package_blobs_data())

    #uart.write("Hello World!\r")
    #uart.write(1+'\n')
    #计算fps
    #print(clock.fps())
