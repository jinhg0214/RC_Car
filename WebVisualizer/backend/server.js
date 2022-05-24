const express = require("express");

const app = express();

const PORT = 8081;

const db = require('./models')

const server =  require('http').createServer(app);
const io = require("socket.io")(server, {
    pingTimeout : 1,
    pingInterval: 5000,
})

app.get('/', async (req,res) => {
    // const result = await db['data'].findAll({
    //     attributes: ['temp']
    // });
    // console.log(result)
})

// 데이터를 DB에서 긁어와서 front단으로 넘겨줌
io.on('connection', async (socket) => {
    const time = await db['sensing_jh'].findAll({
        attributes: ['time']
    });

    const press = await db['sensing_jh'].findAll({
        attributes: ['num1']
    });

    const temp = await db['sensing_jh'].findAll({
        attributes: ['num2']
    });

    const humi = await db['sensing_jh'].findAll({
        attributes: ['num3']
    });
    // console.log(temp)

    const timeMsg = time.map(e => e.dataValues.time)
    const pressMsg = press.map(e => e.dataValues.num1)
    const tempMsg = temp.map(e => e.dataValues.num2)
    const humiMsg = humi.map(e => e.dataValues.num3)

    socket.emit("time", pressMsg)
    socket.emit("press", pressMsg)
    socket.emit("temp", tempMsg)
    socket.emit("humi", humiMsg)
})


server.listen(PORT, () => console.log(`이 서버는 ${PORT}번 포트로 동작하고 있습니다.`))