from flask import Flask, send_file

app = Flask(__name__)

@app.route("/")
def display_table():
    return send_file("shlyapaSave.html")

if __name__ == "__main__":
    app.run(debug=True, port = 5000)