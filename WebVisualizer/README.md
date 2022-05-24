# 개요
- 서버에 저장된 데이터를 이용해 데이터를 시각화하여 보여준다
- 백엔드는 AWS 서버와 통신하여 mySQL 데이터베이스에 저장된 데이터를 가져와 
   프론트에 소켓통신을 이용해 전달해준다
- 프론트는 백엔드로부터 받은 데이터를 ApexChart를 이용해 데이터를 시각화하여 보여준다
- 모듈은 삭제했으니 npm i 로 설치해야 서버 구동 가능

## backend
- Node.js로 구현. 
- npx nodemon server.js로 서버 구동할것

## frontend
- Vue를 이용해 구현.
- Vue Apexchart이용 차트 구현함. 
- npm run serve로 프론트 구동할 것

