from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import psycopg2
import time

import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*")

# ---------------- DB CONNECTION ----------------
conn = None
for i in range(10):
    try:
        conn = psycopg2.connect(
            host="pg-todo",
            database="todo_db",
            user="postgres",
            password="postgres"
        )
        print("Connected to DB")
        break
    except psycopg2.OperationalError:
        print("DB not ready...")
        time.sleep(2)

if conn is None:
    exit(1)

cur = conn.cursor()


# ---------------- TASKS CRUD ----------------
@app.route("/tasks", methods=["GET"])
def get_tasks():
    cur.execute("SELECT * FROM tasks ORDER BY id ASC")
    tasks = cur.fetchall()
    return jsonify([{"id": t[0], "title": t[1]} for t in tasks])


@app.route("/tasks/<int:id>", methods=["GET"])
def get_task(id):
    cur.execute("SELECT * FROM tasks WHERE id=%s", (id,))
    task = cur.fetchone()

    if task:
        return jsonify({"id": task[0], "title": task[1]})

    return jsonify({"error": "Not found"}), 404


@app.route("/tasks", methods=["POST"])
def create_task():
    title = request.json.get("title")

    cur.execute(
        "INSERT INTO tasks (title) VALUES (%s) RETURNING id",
        (title,)
    )

    task_id = cur.fetchone()[0]
    conn.commit()

    task = {"id": task_id, "title": title}

    socketio.emit("task_created", task)

    return jsonify(task)


@app.route("/tasks/<int:id>", methods=["PUT"])
def update_task(id):
    title = request.json.get("title")

    cur.execute(
        "UPDATE tasks SET title=%s WHERE id=%s",
        (title, id)
    )

    conn.commit()

    task = {"id": id, "title": title}

    socketio.emit("task_updated", task)

    return jsonify(task)


@app.route("/tasks/<int:id>", methods=["DELETE"])
def delete_task(id):
    cur.execute("DELETE FROM tasks WHERE id=%s", (id,))
    conn.commit()

    socketio.emit("task_deleted", {"id": id})

    return jsonify({"message": "deleted"})


# ---------------- EMAIL ----------------
@app.route("/send-email", methods=["POST"])
def send_email():
    data = request.json

    to_email = data["to"]
    subject = data["subject"]
    message = data["message"]
    protocol = data["protocol"]

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = "your_email@gmail.com"
    msg["To"] = to_email

    try:
        if protocol == "smtp":
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login("123@gmail.com", "123")
            server.sendmail(msg["From"], [msg["To"]], msg.as_string())
            server.quit()

            return jsonify({"status": "sent via SMTP"})

        elif protocol == "imap":
            return jsonify({
                "status": "IMAP selected",
                "note": "IMAP simulated"
            })

        elif protocol == "pop3":
            return jsonify({
                "status": "POP3 selected",
                "note": "POP3 simulated"
            })

        return jsonify({"error": "Invalid protocol"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)