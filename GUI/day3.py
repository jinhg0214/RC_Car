from PyQt5.QtWidgets import *
from PyQt5.uic import *
from PyQt5 import QtSql
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import time

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("main.ui", self) # pyqt5 로 제작한 gui데이터 가져오기
        
        ## AWS DB 데이터 연동 부분
        self.db = QtSql.QSqlDatabase.addDatabase('QMYSQL')

        self.db.setHostName("### AWS 주소 ###")
        self.db.setDatabaseName("### DB 이름 ###")
        self.db.setUserName("### 사용자 이름 ###")
        self.db.setPassword("### 비밀번호 ###")
        
        ok = self.db.open()
        print(ok)

        # 0.1초 간격으로 명령어 테이블을 확인 후 GUI에 명령어 및 데이터들을 보여줌.
        self.query = QtSql.QSqlQuery()
        self.timer = QTimer()
        self.timer.setInterval(100) # 100 ms
        self.timer.timeout.connect(self.pollingQuery) 
        self.timer.start()

        self.start = 0
        self.end = 0

    # 명령어 테이블 및 센싱 테이블에서 데이터를 가져오는 함수
    # 센싱 테이블에는 차량이 전송한 정보들이 저장되어있다. ex) 온도, 습도, 기압 
    def pollingQuery(self):
        self.query = QtSql.QSqlQuery("select * from command_jh order by time desc limit 5");

        self.text_command.clear()
        while (self.query.next()):
            self.record = self.query.record()
            str = "%s | %10s | %10s | %4d" %(self.record.value(0).toString(), self.record.value(1), self.record.value(2), self.record.value(3))
            self.text_command.setTextColor(QColor(255,255,255))
            self.text_command.append(str)

        # read sensor table
        str = ""
        self.query = QtSql.QSqlQuery("select * from sensing_jh order by time desc limit 5");

        self.text_sensing.clear()
        while (self.query.next()):
            self.record = self.query.record()
            str += "%s | %10s | %10s | %10s \n" %(self.record.value(0).toString(), self.record.value(1), self.record.value(2), self.record.value(3))
            self.text_sensing.setTextColor(QColor(255,255,255))
            self.text_sensing.setText(str)

    # 명령어 전송 함수 
    # 누른 버튼에 따라 그에 맞는 명령어를 테이블에 전송한다.
    def commandQuery(self, cmd, arg):
        self.query.prepare("insert into command_jh(time, cmd_string, arg_string, is_finish) values(:time, :cmd, :arg, :finish)");
        time = QDateTime().currentDateTime()
        self.query.bindValue(":time", time)
        self.query.bindValue(":cmd", cmd)
        self.query.bindValue(":arg", arg)
        self.query.bindValue(":finish", 0)
        self.query.exec()

    # GUI에서 GO 버튼을 누르면 호출 되는 함수
    # 즉 , mySQL에 "INSERT INTO `명령어 테이블" value(:시간, :앞으로, :1초동안, "수행여부")가 전달된다 
    def clickedGo(self): 
        self.commandQuery("go", "1 sec")
        print("GO")

    def clickedBack(self):
        self.commandQuery("back", "1 sec")
        print("BACK")

    def clickedStop(self):
        self.commandQuery("stop", "1 sec")
        print("STOP")
        
    # 버튼이 눌린 시간만큼 바퀴가 움직인다.
    # 바퀴가 움직이는건 차량측에서 계산하고, GUI측에서는 누른 시간만 계산하여 매개변수로 전달한다
    def left_pressed(self):
        self.start = time.time()

    def left_released(self):
        self.end = time.time()
        elapsed = self.end - self.start
        timestr = str(round(elapsed, 2)) + " sec"
        self.commandQuery("left", timestr);
        print("left")

    def right_pressed(self):
        self.start = time.time()

    def right_released(self):
        self.end = time.time()
        elapsed = self.end - self.start
        timestr = str(round(elapsed, 2)) + " sec"
        self.commandQuery("right", timestr);
        print("right")

    # 바퀴를 가운데 정렬하는 함수
    def clickedMid(self):
        self.commandQuery("mid", "1 sec");
        print("mid");
    
    # ADV 이동
    # 누르고있는 동안에만 움직인다
    # 매개변수로 press, release를 전달한다
    def LeftsidePress(self):
        self.commandQuery("leftside", "press")
        print("left Release") 

    def LeftsideRelease(self):
        self.commandQuery("leftside", "release")
        print("left Release")

    def FrontPress(self):
        self.commandQuery("front", "press")
        print("front Press")

    def FrontRelease(self):
        self.commandQuery("front", "release")
        print("front Release")

    def RightsidePress(self):
        self.commandQuery("rightside", "press")
        print("right Press")

    def RightsideRelease(self):
        self.commandQuery("rightside", "release")
        print("right Release")


app = QApplication([])
win = MyApp()
win.show()
app.exec()
