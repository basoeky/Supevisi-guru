from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "Backend Supervisi Guru Aktif!"})

# Jika Anda memiliki route lain dari aplikasi asli Anda, 
# paste kode route aplikasi Anda di sini.
