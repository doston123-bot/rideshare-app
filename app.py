from flask import Flask, request, jsonify
import sqlite3
import random

app = Flask(__name__)

# -------- DB --------
def db():
    return sqlite3.connect("app.db")

conn = db()
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, phone TEXT, code TEXT)")
c.execute("""
CREATE TABLE IF NOT EXISTS rides(
    id INTEGER PRIMARY KEY,
    driver TEXT,
    f TEXT,
    t TEXT,
    time TEXT,
    passengers TEXT
)
""")

conn.commit()
conn.close()

# -------- AUTH --------
@app.route("/send_code", methods=["POST"])
def send_code():
    data = request.json
    phone = data["phone"]
    code = str(random.randint(1000, 9999))

    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO users(phone,code) VALUES(?,?)", (phone, code))
    conn.commit()
    conn.close()

    print("CODE:", code)

    return jsonify({"ok":1})

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    phone = data["phone"]
    code = data["code"]

    conn = db()
    c = conn.cursor()
    c.execute("SELECT code FROM users WHERE phone=? ORDER BY id DESC", (phone,))
    row = c.fetchone()
    conn.close()

    if row and row[0] == code:
        return jsonify({"ok":1})
    return jsonify({"ok":0})

# -------- RIDES --------
@app.route("/add", methods=["POST"])
def add():
    data = request.json
    conn = db()
    c = conn.cursor()

    c.execute("""
    INSERT INTO rides(driver,f,t,time,passengers)
    VALUES (?,?,?,?,?)
    """, (data["user"], data["from"], data["to"], data["time"], ""))

    conn.commit()
    conn.close()
    return jsonify({"ok":1})

@app.route("/join", methods=["POST"])
def join():
    data = request.json
    ride_id = data["ride_id"]
    user = data["user"]

    conn = db()
    c = conn.cursor()

    c.execute("SELECT passengers FROM rides WHERE id=?", (ride_id,))
    row = c.fetchone()

    passengers = row[0] or ""

    if user not in passengers:
        passengers += user + ","

    c.execute("UPDATE rides SET passengers=? WHERE id=?",
              (passengers, ride_id))

    conn.commit()
    conn.close()

    return jsonify({"ok":1})

@app.route("/rides")
def rides():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM rides")
    data = c.fetchall()
    conn.close()
    return jsonify(data)

# -------- FRONT --------
@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html>
<head>
<title>RideShare PRO</title>

<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<style>
body {
    margin:0;
    font-family:Arial;
    color:white;
    background:url('https://images.unsplash.com/photo-1503376780353-7e6692767b70') no-repeat center;
    background-size:cover;
}

.box {
    backdrop-filter: blur(10px);
    padding:20px;
    text-align:center;
}

input, button {
    padding:10px;
    margin:5px;
    border-radius:8px;
    border:none;
}

button {
    background:#6366f1;
    color:white;
    cursor:pointer;
    transition:0.3s;
}

button:hover { transform:scale(1.05); }

.card {
    background:rgba(0,0,0,0.5);
    padding:10px;
    margin:10px;
    border-radius:10px;
    animation:fade 0.5s;
}

@keyframes fade {
    from {opacity:0; transform:translateY(20px);}
    to {opacity:1;}
}

#map { height:300px; margin-top:20px; border-radius:10px; }
</style>
</head>

<body>

<div class="box">

<h2>📱 Регистрация</h2>

<input id="phone" placeholder="+998...">
<button onclick="sendCode()">Отправить код</button>

<br>

<input id="code" placeholder="Код">
<button onclick="login()">Войти</button>

<hr>

<div id="app" style="display:none">

<h2>🚗 RideShare</h2>

<input id="from" placeholder="From">
<input id="to" placeholder="To">
<input type="datetime-local" id="time">

<button onclick="addRide()">Создать поездку</button>

<div id="rides"></div>

<div id="map"></div>

</div>

</div>

<script>
var user = "";

// 📱 код
function sendCode(){
    fetch("/send_code",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            phone:document.getElementById("phone").value
        })
    });
    alert("Код смотри в Render Logs");
}

// 🔐 вход
function login(){
    fetch("/verify",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            phone:document.getElementById("phone").value,
            code:document.getElementById("code").value
        })
    })
    .then(r=>r.json())
    .then(data=>{
        if(data.ok){
            user = document.getElementById("phone").value;
            document.getElementById("app").style.display="block";
        } else {
            alert("Неверный код");
        }
    });
}

// 🚗 создать
function addRide(){
    fetch("/add",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            user:user,
            from:document.getElementById("from").value,
            to:document.getElementById("to").value,
            time:document.getElementById("time").value
        })
    });
}

// 🚗 попутчик
function joinRide(id){
    fetch("/join",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            ride_id:id,
            user:user
        })
    });
}

// 📍 карта
var map = L.map('map').setView([41.31,69.27],11);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
.addTo(map);

navigator.geolocation.getCurrentPosition(pos=>{
    L.marker([pos.coords.latitude,pos.coords.longitude])
    .addTo(map).bindPopup("You");
});

// 🔄 обновление
function load(){
    fetch("/rides").then(r=>r.json()).then(data=>{
        let html="";
        data.forEach((r,i)=>{
            html += `<div class="card">
            🚗 Водитель: ${r[1]} <br>
            📍 ${r[2]} → ${r[3]} <br>
            ⏰ ${r[4]} <br>
            👥 ${r[5] || "нет пассажиров"} <br><br>

            <button onclick="joinRide(${r[0]})">
            🚗 Поехать
            </button>
            </div>`;

            let lat = 41.31 + i*0.02;
            let lng = 69.27 + i*0.02;
            L.marker([lat,lng]).addTo(map);
        });
        document.getElementById("rides").innerHTML = html;
    });
}

setInterval(load,2000);

</script>

</body>
</html>
"""
