from flask import Flask, request, jsonify
import sqlite3
import random

app = Flask(__name__)

# ---------------- DATABASE ----------------
def db():
    return sqlite3.connect("app.db")

conn = db()
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS rides(id INTEGER PRIMARY KEY, user TEXT, f TEXT, t TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, user TEXT, text TEXT)")
conn.commit()
conn.close()

# ---------------- API ----------------
@app.route("/add_ride", methods=["POST"])
def add_ride():
    data = request.json
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO rides(user,f,t) VALUES(?,?,?)",
              (data["user"], data["from"], data["to"]))
    conn.commit()
    conn.close()
    return jsonify({"status":"ok"})

@app.route("/rides")
def rides():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM rides")
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/send_msg", methods=["POST"])
def send_msg():
    data = request.json
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO messages(user,text) VALUES(?,?)",
              (data["user"], data["text"]))
    conn.commit()
    conn.close()
    return jsonify({"ok":1})

@app.route("/msgs")
def msgs():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM messages")
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

# ---------------- FRONT ----------------
@app.route("/")
def index():
    return """
    <html>
    <head>
    <title>RideShare MAX</title>

    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

    <style>
    body {background:#0b1220;color:white;font-family:Arial;text-align:center}
    input,button {padding:10px;margin:5px}
    #map {height:300px;margin-top:20px}
    </style>
    </head>

    <body>

    <h1>🚗 RideShare MAX</h1>

    <input id="user" placeholder="Name">

    <h3>Создать поездку</h3>
    <input id="from" placeholder="From">
    <input id="to" placeholder="To">
    <button onclick="addRide()">Create</button>

    <div id="rides"></div>

    <div id="map"></div>

    <h3>💬 Chat</h3>
    <div id="chat"></div>

    <input id="msg" placeholder="Message">
    <button onclick="sendMsg()">Send</button>

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
        fetch("/add_ride",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                user:document.getElementById("user").value,
                from:document.getElementById("from").value,
                to:document.getElementById("to").value
            })
        });
    }

    function loadRides(){
        fetch("/rides").then(r=>r.json()).then(data=>{
            let html="";
            data.forEach(r=>{
                html += `<p>${r[1]}: ${r[2]} → ${r[3]}</p>`;
            });
            document.getElementById("rides").innerHTML = html;
        });
    }

    function sendMsg(){
        fetch("/send_msg",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                user:document.getElementById("user").value,
                text:document.getElementById("msg").value
            })
        });
    }

    function loadChat(){
        fetch("/msgs").then(r=>r.json()).then(data=>{
            let html="";
            data.forEach(m=>{
                html += `<p><b>${m[1]}</b>: ${m[2]}</p>`;
            });
            document.getElementById("chat").innerHTML = html;
        });
    }

    // 🔄 автообновление
    setInterval(()=>{
        loadRides();
        loadChat();
    }, 2000);

    </script>

    </body>
    </html>
    """
