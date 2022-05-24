import sys
sys.path.append('./Raspi-MotorHAT-python3') # 모터 제어를 위한 MotorHAT 라이브러리 이용

from Raspi_MotorHAT import Raspi_MotorHAT, Raspi_DCMotor
from Raspi_PWM_Servo_Driver import PWM
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtSql

from sense_hat import SenseHat # 센스햇 라이브러리 이용

# 음성제어를 위한 라이브러리들
import asyncio
import websockets

import atexit
import time

###########################  전역변수들  #################################################

# 차량 모터 제어 관련
mh = Raspi_MotorHAT(addr=0x6f)
myMotor = mh.getMotor(2)
myMotor.setSpeed(100)

pwm = PWM(0x6F)
pwm.setPWMFreq(60)
        
# motor control
gear = 0  # 차량 기어 몇단인지
speed = 0 # 최종 결정 속도 ( 0 ~ 255 )
movedir = 1 # 1: foward, -1: backward
steer = 355 # 서보모터를 통한 조향 ( 250 ~ 350(중앙) ~ 450)
        
# 명령 모드 관련
mode_list = []
mode_index = 0
current_mode = None

# 센스햇 관련
sense = SenseHat()
sense.set_imu_config(True, True, True)

last_command = ""

p = 0.0
t = 0.0
h = 0.0

# 초기 display 값
rainbow = [
    [255, 0, 0], [255, 0, 0], [255, 87, 0], [255, 196, 0], [205, 255, 0], [95, 255, 0], [0, 255, 13], [0, 255, 122],
    [255, 0, 0], [255, 96, 0], [255, 205, 0], [196, 255, 0], [87, 255, 0], [0, 255, 22], [0, 255, 131], [0, 255, 240],
    [255, 105, 0], [255, 214, 0], [187, 255, 0], [78, 255, 0], [0, 255, 30], [0, 255, 140], [0, 255, 248], [0, 152, 255],
    [255, 223, 0], [178, 255, 0], [70, 255, 0], [0, 255, 40], [0, 255, 148], [0, 253, 255], [0, 144, 255], [0, 34, 255],
    [170, 255, 0], [61, 255, 0], [0, 255, 48], [0, 255, 157], [0, 243, 255], [0, 134, 255], [0, 26, 255], [83, 0, 255],
    [52, 255, 0], [0, 255, 57], [0, 255, 166], [0, 235, 255], [0, 126, 255], [0, 17, 255], [92, 0, 255], [201, 0, 255],
    [0, 255, 66], [0, 255, 174], [0, 226, 255], [0, 117, 255], [0, 8, 255], [100, 0, 255], [210, 0, 255], [255, 0, 192],
    [0, 255, 183], [0, 217, 255], [0, 109, 255], [0, 0, 255], [110, 0, 255], [218, 0, 255], [255, 0, 183], [255, 0, 74]
]

##########################################################################################
# 각종 모드들
# 모드들은 모두 update 메서드들을 가지고있고, 메인에서 각 클래스의 update를 호출한다

# 1. default mode
# 디폴트 모드에서는 센스햇에 무지개 색상을 계속 바꿔가며 출력한다
class Default_Mode():
    global sense

    def msleep(self, x):
        return time.sleep(x/1000.0)
    #msleep = lambda x:[time.sleep(x / 1000.0)]

    def next_colour(self, pix):
        r = pix[0]
        g = pix[1]
        b = pix[2]

        if (r == 255 and g < 255 and b == 0):
            g += 1

        if (g == 255 and r > 0 and b == 0):
            r -= 1

        if (g == 255 and b < 255 and r == 0):
            b += 1

        if (b == 255 and g > 0 and r == 0):
            g -= 1

        if (b == 255 and r < 255 and g == 0):
            r += 1

        if (r == 255 and b > 0 and g == 0):
            b -= 1

        pix[0] = r
        pix[1] = g
        pix[2] = b

    # 클래스의 메인함수.
    # 스레드가 주기적으로 update 함수를 호출한다
    def update(self):
        print(f"======== Default Mode ========")
        while mode_index == 0:
            for pix in rainbow:
                self.next_colour(pix)
            
            sense.set_pixels(rainbow)
            self.msleep(2)


# 명령어 모드 클래스
# 가장 최근에 수행한 명령을 아이콘으로 표시한다
class Command_Mode():
    global last_command

    def __init__(self):
        # 명령어 모드에서만 사용하는 이미지들이므로, 내부에 멤버변수로 선언했음
        w = (150, 150, 150)
        e = (0, 0, 0)
        r = (255, 0, 0)
        self.stopImage = [ # 정지 이미지
            e,e,r,r,r,r,e,e,
            e,r,r,r,r,r,r,e,
            r,r,r,r,r,r,r,r,
            r,w,w,w,w,w,w,r,
            r,w,w,w,w,w,w,r,
            r,r,r,r,r,r,r,r,
            e,r,r,r,r,r,r,e,
            e,e,r,r,r,r,e,e,
        ]
        self.arrowImage = [ # 전방 화살표 
            e,e,e,r,e,e,e,e,
            e,e,r,r,e,e,e,e,
            e,r,w,r,r,r,r,r,
            r,w,w,w,w,w,w,r,
            e,r,w,r,r,r,r,r,
            e,e,r,r,e,e,e,e,
            e,e,e,r,e,e,e,e,
            e,e,e,e,e,e,e,e,
        ]
        self.arrowImage2 = [ # 오른쪽 화살표
            e,e,e,r,e,e,e,e,
            e,e,r,w,r,e,e,e,
            e,r,w,w,w,r,e,e,
            r,r,r,w,r,r,r,e,
            e,e,r,w,r,e,e,e,
            e,e,r,w,r,e,e,e,
            e,e,r,w,r,e,e,e,
            e,e,r,r,r,e,e,e,
        ]
        self.arrowImage3 = [ # 대각선 오른쪽 화살표
            r,r,r,r,r,e,e,e,
            r,w,w,r,e,e,e,e,
            r,w,w,r,e,e,e,e,
            r,r,r,w,r,e,e,e,
            r,e,e,r,w,r,e,e,
            e,e,e,e,r,w,r,e,
            e,e,e,e,e,r,w,r,
            e,e,e,e,e,e,r,e,
        ]
        self.midImage = [ # 중앙 정렬 이미지
            e,r,r,r,r,r,e,e,
            e,e,r,r,r,e,e,e,
            e,e,e,r,e,e,e,e,
            w,w,w,w,w,w,w,w,
            w,w,w,w,w,w,w,w,
            e,e,e,r,e,e,e,e,
            e,e,r,r,r,e,e,e,
            e,r,r,r,r,r,e,e,
        ]

    def update(self): 
        print(f"===== Command Mode =====")

        # 로딩 이미지
        sense.set_pixels(rainbow)
        time.sleep(0.5)

        # 가장 최근에 수행한 명령어를 확인후 그에 맞는 이미지 출력
        while mode_index == 1:
            if last_command == "stop":
                sense.set_pixels(self.stopImage)
            elif last_command == "go" or last_command == "front":
                sense.set_pixels(self.arrowImage) 
            elif last_command == "back":
                sense.set_pixels(self.arrowImage)
                sense.flip_h()
            elif last_command == "left":
                sense.set_pixels(self.arrowImage2)
                sense.flip_v()
            elif last_command == "right" :
                sense.set_pixels(self.arrowImage2)
            elif last_command == "mid":
                sense.set_pixels(self.midImage)
            elif last_command == "leftside":
                sense.set_pixels(self.arrowImage3)
                sense.flip_v()
            elif last_command == "rightside":
                sense.set_pixels(self.arrowImage3)
            time.sleep(1)


# 온도와 습도를 콘솔과 센스햇에 출력하는 클래스
class Temp_Humi_Mode():
    global sense, p, t, h

    def update(self):
        print(f"===== Temperature and humidity mode =====")
        
        # 로딩 이미지
        sense.set_pixels(rainbow)
        time.sleep(0.5)

        # 압력은 앞 두줄에, 온도는 중간 두줄에, 습도는 마지막 두줄에 색상으로 표시한다
        # 압력 : 파랑(950) < 초록 < 빨강(1050)
        # 온도 : 파랑(25) < 초록 < 빨강(35)
        # 습도 : 노랑(40) < 초록 < 파랑(60)
        while mode_index == 2:
            sense.clear()
            # p 0~1
            if p < 950 : # pressure too low
                for y in range(8):
                    for x in range(2):
                        sense.set_pixel(x, y, 0, 0, 255)
            
            elif p > 1050 : # pressure too high
                for y in range(8):
                    for x in ragne(2):
                        sense.set_pixel(x, y, 255, 0, 0)
            else:
                for y in range(8): # proper pressure
                    for x in range(2):
                        sense.set_pixel(x, y, 127, 255, 0)
            # t 2~4
            if t < 25 : # temp too low
                for y in range(8):
                    for x in range(3,5):
                        sense.set_pixel(x, y, 0, 0, 255)
            elif t > 35 : # temp too high
                for y in range(8):
                    for x in range(3,5):
                        sense.set_pixel(x, y, 255, 0, 0)
            else: # proper temp
                for y in range(8):
                    for x in range(3,5):
                        sense.set_pixel(x, y, 127, 255, 0)
            # h 5~7 
            if h < 40 : # super dry
                for y in range(8):
                    for x in range(6,8):
                        sense.set_pixel(x, y, 255, 255, 0) # yellow
            elif h > 60 : # super wet
                for y in range(8):
                    for x in range(6, 8):
                        sense.set_pixel(x, y, 0, 0, 255) 
            else : # proper humi
                for y in range(8):
                    for x in range(6, 8):
                        sense.set_pixel(x, y, 127, 255, 0)
            
            # sense.show_message(str(t))
            msg = "Press : " + str(p) + " Temp : " + str(t) + " Humid : " + str(h)
            print(msg)
 
            time.sleep(1)


# 자이로 센서를 이용해 roll pitch yaw를 출력한다
# 또한 읽은 roll pitch를 이용해, 센서햇 위에서 공을 움직인다
class Gyro_Mode():
    global sense
    def __init__(self):
        self.x = 5
        self.y = 5
        self.r = 255
        self.g = 255
        self.b = 255
        self.roll = 0
        self.pitch = 0
        self.yaw = 0   
        
    def update_screen(self):
        sense.clear()
        sense.set_pixel(self.x, self.y, self.r, self.g, self.b)

    def clam(self, val, min_val = 0, max_val =7):
        return min(max_val, max(min_val, val))

    def move_dot(self, pitch, roll, x, y):
        new_x = x
        new_y = y
        if 15 < pitch < 180 and x!= 0:
            new_x -= 1
        elif 345 > pitch > 181 and x!= 7:
            new_x += 1
        if 15 < roll < 180 and y != 7:
            new_y += 1
        elif 345 > roll > 181 and y!= 0:
            new_y -= 1

        return new_x, new_y

    def update(self):
        print("===== Gyro Mode =====")
        
        sense.set_pixels(rainbow)
        time.sleep(0.5)
        
        while mode_index == 3:
            # roll, pitch, yaw
            orientation = sense.get_orientation_degrees()
            self.pitch = orientation["pitch"]
            self.roll = orientation["roll"]
            self.yaw = orientation["yaw"]
            
            self.x, self.y = self.move_dot(self.pitch, self.roll, self.x, self.y)
            self.update_screen()

            print("p : {:.0f}, r : {:.0f}, y : {:.0f}" .format(self.pitch, self.roll, self.yaw))
            raw = sense.get_accelerometer_raw()

            # 온도에따라 공의 색상이 바뀌도록 한다
            temp = sense.get_temperature()

            # print("Temperature : {:1f}'C" .format(temp))
            if temp < 25:
                r = 0
                g = 0
                b = 255
            elif temp > 35:
                r = 255
                g = 0
                b = 0
            else :
                r = 255
                g = 255
                b = 255

            time.sleep(0.1)

############## 센서햇의 조이스틱 매핑 #############
# 센서햇의 조이스틱을 누르면 모드가 변경된다
def pushed_middle(event):
    global mode_index
    if event.action == 'pressed':
        mode_index = mode_index + 1
        if mode_index > len(mode_list) - 1:
            mode_index = 0

sense.stick.direction_middle = pushed_middle

##################################################

# 센서햇 관련 스레드
# 조이스틱의 입력을 확인하면서, 모드가 변경되는지 확인한다
# 모드가 변경되면 그에 맞는 모드를 출력한다
class senseThread(QThread):
    def __init__(self):
        super().__init__()

    # sense Thread main
    def run(self):
        global mode_list
        mode_list = [Default_Mode(), Command_Mode(), Temp_Humi_Mode(), Gyro_Mode()]
        global mode_index
        mode_index = 0
        global current_mode

        while True:
            current_mode = mode_list[mode_index]
            current_mode.update()
            time.sleep(1)


# 차량 관련 처리 클래스
# DB에서 command 테이블을 읽고, 가장 최근의 명령을 처리한다
# 또한 센스햇을 이용해 읽은 데이터들을 DB에 올린다
class pollingThread(QThread):
    def __init__(self):
        super().__init__()

        global myMotor, pwm # 전역변수 DC모터와 서보모터를 가져와 제어
        global gear, speed, movedir, steer 
    
    def run(self):

        # 초기 AWS DB 연결 세팅 부분
        self.db = QtSql.QSqlDatabase.addDatabase("QMYSQL")
        self.db.setHostName("### 아마존 웹 서버 주소")
        self.db.setDatabaseName("### DB 이름 ###")
        self.db.setUserName("### 사용자 이름 ###")
        self.db.setPassword("### 비밀번호 ###")
        ok = self.db.open()
        print(ok) 

        interval = 0

        # 0.1초 간격으로 command 테이블을 불러오고
        # 5초 간격으로 senser 테이블에 저장한다
        
        # before start infinity loop, first clear tables for storage
        query = QtSql.QSqlQuery("delete from command_jh")  
        # 이전의 command 테이블에 들어있던 내용은 모두 삭제한다 
        
        while True:
            time.sleep(0.1) # 100 ms 
            if interval > 20: # 2sec
                self.setQuery()
                interval = 0
            self.getQuery()
            interval = interval + 1
    
    # 데이터베이스에 읽은 데이터를 저장하는 메서드
    def setQuery(self):
        pressure = sense.get_pressure()
        temp = sense.get_temperature()
        humidity = sense.get_humidity()
        global p, t, h
        p = round(pressure, 2)
        t = round(temp, 2)
        h = round(humidity, 2)

        #msg = "Press : " + str(p) + " Temp : " + str(t) + " Humid : " + str(h)
        #print(msg)
        
        #query = QtSql.QSqlQuery("delete from sensing_jh where time is not null order by time asc limit 1") 
        # # 데이터베이스가 꽉차는걸 막기 위해 가장 오래된 데이터를 하나 삭제한다

        query = QtSql.QSqlQuery()
        query.prepare("insert into sensing_jh(time, num1, num2, num3, meta_string, is_finish) values(:time, :num1, :num2, :num3, :meta, :finish)");

        time = QDateTime().currentDateTime()
        query.bindValue(":time", time)
        query.bindValue(":num1", p)
        query.bindValue(":num2", t)
        query.bindValue(":num3", h)
        query.bindValue(":meta", "")
        query.bindValue(":finish", 0)

        query.exec() 

    # command 테이블을 읽고, 모터 관련 명령을 수행하는 메서드
    def getQuery(self):
        global gear, speed, steer, last_command
        query = QtSql.QSqlQuery("select * from command_jh order by time desc limit 1");
        query.next()
        cmdTime = query.record().value(0)
        cmdType = query.record().value(1)
        
        last_command = cmdType

        cmdArg = query.record().value(2)
        is_finish = query.record().value(3)
        #print("is_finish = " + str(is_finish))
        if is_finish == 0:
            #detect new command
            #print(cmdTime.toString(), cmdType, cmdArg)
            
            #update
            query = QtSql.QSqlQuery("update command_jh set is_finish=1 where is_finish=0"); 
    
            # basic movement
            if cmdType == "go": self.go()
            if cmdType == "back" : self.back()
            if cmdType == "left" : self.left(cmdArg)
            if cmdType == "right" : self.right(cmdArg)
            if cmdType == "stop" : self.stop()
            if cmdType == "mid" : self.DirFoward()
            
            # adv movement
            if cmdType == "front" and cmdArg == "press":
                gear=1
                self.go() # speed 100
                self.DirFoward()
            if cmdType == "front" and cmdArg == "release":
                self.stop()

            # 핸들 가장 왼쪽으로 틀고 전진 (왼쪽 원 그리기)
            if cmdType == "leftside" and cmdArg == "press":
                steer = 275
                pwm.setPWM(0, 0, steer) # Left Square
                gear=1
                self.go()
            if cmdType == "leftside" and cmdArg == "release":
                self.stop()

            # 핸들 가장 오른쪽으로 틀고 전진 (오른쪽 원 그리기)
            if cmdType == "rightside" and cmdArg == "press":
                steer = 425
                pwm.setPWM(0, 0, steer) # Right Square
                gear=1
                self.go()
            if cmdType == "rightside" and cmdArg == "release":
                self.stop()
                
    # 이동
    def move(self, gear):
        # set speed
        global speed
        speed = gear * 50
        if speed > 0:
            myMotor.setSpeed(speed)
            movedir = 1
        elif speed < 0:
            myMotor.setSpeed(speed * -1)
            movedir = -1
        else:
            movedir = 0

        #foward, backward
        if movedir == 1:
            myMotor.run(Raspi_MotorHAT.FORWARD)
        elif movedir == -1:
            myMotor.run(Raspi_MotorHAT.BACKWARD)
        else :
            myMotor.run(Raspi_MotorHAT.RELEASE)
        #print(f"gear:{gear}, speed:{speed}, dir:{movedir}")

    # 기어 1단 증가
    def go(self):
        global speed, gear
        #print("MOTOR GO")
        # change gear
        gear = gear + 1
        if gear > 5:
            gear = 5

        self.move(gear)

    # 기어 1단 감소
    def back(self):
        global speed, gear
        #print("MOTOR BACK")
        # change gear
        gear = gear - 1
        if gear < -5:
            gear = 0
        
        self.move(gear)

    # 정지
    def stop(self):
        global speed, gear
        speed = 0
        gear = 0
        myMotor.setSpeed(speed)
        myMotor.run(Raspi_MotorHAT.RELEASE)

    # 누른 시간만큼 핸들 왼쪽으로 틀기
    def left(self, timeArg):
        global steer
        #print(f"MOTOR LEFT : {timeArg}")
        # 0.1sec = about 10 pwm
        li = timeArg.split(' ')
        
        steer = steer + int(float(li[0]) * 100) * -1 # move left side
        
        if steer < 250:
            steer = 250
        #print(steer)
        pwm.setPWM(0, 0, steer)

    # 누른 시간만큼 핸들 오른쪽으로 틀기
    def right(self, timeArg):
        global steer
        #print(f"MOTOR RIGHT : {timeArg}")
        li = timeArg.split(' ')

        steer = steer + int(float(li[0]) * 100) * 1 # move right

        if steer > 450 :
            steer = 450
        #print(steer)
        pwm.setPWM(0,0, steer)

    # 핸들 중앙정렬
    def DirFoward(self):
        global steer
        #print("MOTOR MID")
        steer = 355
        pwm.setPWM(0,0, steer)

#################################################
# 정보 보호를 위해 지웠음 IP와 PORT는 자신의 정보에 맞게 넣을것
ServerIP = 'INSERT MYSERVERIP' # 소켓 통신을위한 차량의 아이피를 넣을것
WebsocketPort = PORT # 포트도
#################################################

def mic_go():
    global gear, speed, myMotor
    gear = 2
    speed = gear * 50
    myMotor.setSpeed(speed)
    myMotor.run(Raspi_MotorHAT.FORWARD)
    last_command = "go"

def mic_back():
    global gear, speed, myMotor
    gear = 2
    speed = gear * 50
    myMotor.setSpeed(speed)
    myMotor.run(Raspi_MotorHAT.BACKWARD)
    last_command = "back"

def mic_stop():
    global gear, speed, myMotor
    gear = 0
    speed = gear * 50
    myMotor.setSpeed(speed)
    myMotor.run(Raspi_MotorHAT.RELEASE)
    last_command = "stop"

def mic_left():
    global steer, pwm
    steer = 275
    pwm.setPWM(0, 0, steer)
    last_command = "left"

def mic_right():
    global steer, pwm
    steer = 425
    pwm.setPWM(0, 0, steer)
    last_command = "right"

def mic_dirFoward():
    global steer, pwm
    steer = 355
    pwm.setPWM(0, 0, steer)
    last_command = "mid"

command = ['전진', '후진', '정지', '왼쪽', '오른쪽', '중앙']
func = [mic_go, mic_back, mic_stop, mic_left, mic_right, mic_dirFoward]

# 비동기 통신을 이용한 음성 인식 메서드
# 마이크로 음성을 전달하면, 구글 Speech-to-text를 이용해 음성을 텍스트로 변환한다.
# 텍스트로 변환된 명령어를 확인 후, 이를 수행한다.
async def voice_drive(websocket, path):
    try:
        loop = asyncio.get_running_loop()   # asyncio 이벤트루프

        while True:
            # 클라이언트로부터 메시지 받음
            message = await websocket.recv()
            #print(f'message: {message}')
            # 메시지에 해당하는  index의 func 실행
            if message in command:
                print('massage matches.')
                await loop.run_in_executor(None, func[command.index(message)]) # run_in_executor() 사용해 별도 스레드에서 비동기적으로 함수 실행

                response = 'OK' # 확인 후 성공적으로 수행했음을 알림
            else:
                print('not a commmand')
                response = 'not a command'
            # 응답 보냄
            await websocket.send(response)
    
    except websockets.ConnectionClosed:
        print('네크워크 확인')

async def main():
    try:
        # websocket 서버 작동
        server = await websockets.serve(voice_drive, host = ServerIP, port = WebsocketPort)
        print('voice recognition server ready!')
        await server.wait_closed()

    except KeyboardInterrupt:
        print('\n사용자의 요청으로 종료합니다...')
    except:
        print('\n확인되지 않은 오류입니다...')
    finally:
        pass
        #motor1.run(Raspi_MotorHAT.RELEASE)  # 종료시 모터 멈춤
    
if __name__ == '__main__':
    th1 = pollingThread()
    th2 = senseThread()

    th1.start()
    th2.start()

    app = QApplication([])
    asyncio.run(main())

    while True:
        pass
