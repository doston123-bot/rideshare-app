from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def db():
    return sqlite3.connect("app.db")

# -------- DB --------
conn = db()
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS rides(id INTEGER PRIMARY KEY, user TEXT, f TEXT, t TEXT, time TEXT)")
conn.commit()
conn.close()

# -------- API --------
@app.route("/add", methods=["POST"])
def add():
    data = request.json
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO rides(user,f,t,time) VALUES(?,?,?,?)",
              (data["user"], data["from"], data["to"], data["time"]))
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

.container {
    backdrop-filter: blur(10px);
    padding:20px;
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

button:hover {
    transform:scale(1.05);
}

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

#map {
    height:300px;
    margin-top:20px;
    border-radius:10px;
}
</style>
</head>

<body>

<div class="container">

<h1>🚗 RideShare</h1>

<input id="user" placeholder="Name">

<h3>Создать поездку</h3>
<input id="from" placeholder="From">
<input id="to" placeholder="To">
<input type="datetime-local" id="time">

<button onclick="addRide()">Создать</button>

<h3>Поездки</h3>
<div id="rides"></div>

<div id="map"></div>

</div>

<script>

var map = L.map('map').setView([41.31,69.27],11);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
.addTo(map);

// 📍 GPS
navigator.geolocation.getCurrentPosition(pos=>{
    L.marker([pos.coords.latitude,pos.coords.longitude])
    .addTo(map).bindPopup("You");
});

function addRide(){
    fetch("/add",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            user:document.getElementById("user").value,
            from:document.getElementById("from").value,
            to:document.getElementById("to").value,
            time:document.getElementById("time").value
        })
    });
}

function load(){
    fetch("/rides").then(r=>r.json()).then(data=>{
        let html="";
        data.forEach((r,i)=>{
            html += `
            <div class="card">
            👤 ${r[1]} <br>
            📍 ${r[2]} → ${r[3]} <br>
            ⏰ ${r[4]}
            </div>`;

            let lat = 41.31 + i*0.02;
            let lng = 69.27 + i*0.02;

            L.marker([lat,lng]).addTo(map);
        });

        document.getElementById("rides").innerHTML = html;
    });
}

setInterval(load, 2000);

</script>

</body>
</html>
"""
