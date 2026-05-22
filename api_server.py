from flask import Flask, jsonify, request
import threading
import time
import sys

sys.path.append("/home/ubuntu/upload")
import spamsdt_cleaned

app = Flask(__name__)

active_tasks = {}

def run_sms_task(phone, count, task_id):
    active_tasks[task_id] = "Running SMS"
    try:
        spamsdt_cleaned.worker_sms(phone, count)
        active_tasks[task_id] = "Completed SMS"
    except Exception as e:
        active_tasks[task_id] = f"Error SMS: {str(e)}"

def run_call_task(phone, count, task_id):
    active_tasks[task_id] = "Running Call"
    try:
        spamsdt_cleaned.worker_call(phone, count)
        active_tasks[task_id] = "Completed Call"
    except Exception as e:
        active_tasks[task_id] = f"Error Call: {str(e)}"

def run_both_task(phone, sms_count, call_count, task_id):
    active_tasks[task_id] = "Running Both SMS & Call"
    try:
        threads = []

        if sms_count > 0:
            t_sms = threading.Thread(
                target=spamsdt_cleaned.worker_sms,
                args=(phone, sms_count)
            )
            threads.append(t_sms)
            t_sms.start()

        if call_count > 0:
            t_call = threading.Thread(
                target=spamsdt_cleaned.worker_call,
                args=(phone, call_count)
            )
            threads.append(t_call)
            t_call.start()

        for t in threads:
            t.join()

        active_tasks[task_id] = "Completed Both"

    except Exception as e:
        active_tasks[task_id] = f"Error Both: {str(e)}"

@app.route("/")
def home():
    return jsonify({
        "message": "API Running",
        "endpoints": [
            "/spam/sms",
            "/spam/call",
            "/spam/both",
            "/status/<task_id>"
        ]
    })

@app.route("/spam/sms")
def spam_sms():
    phone = request.args.get("phone")
    count = int(request.args.get("count", 1))

    task_id = f"sms_{phone}_{int(time.time())}"

    threading.Thread(
        target=run_sms_task,
        args=(phone, count, task_id)
    ).start()

    return jsonify({
        "message": "SMS task started",
        "task_id": task_id,
        "phone": phone,
        "count": count
    })

@app.route("/spam/call")
def spam_call():
    phone = request.args.get("phone")
    count = int(request.args.get("count", 1))

    task_id = f"call_{phone}_{int(time.time())}"

    threading.Thread(
        target=run_call_task,
        args=(phone, count, task_id)
    ).start()

    return jsonify({
        "message": "Call task started",
        "task_id": task_id,
        "phone": phone,
        "count": count
    })

@app.route("/spam/both")
def spam_both():
    phone = request.args.get("phone")
    sms_count = int(request.args.get("sms_count", 1))
    call_count = int(request.args.get("call_count", 1))

    task_id = f"both_{phone}_{int(time.time())}"

    threading.Thread(
        target=run_both_task,
        args=(phone, sms_count, call_count, task_id)
    ).start()

    return jsonify({
        "message": "Both task started",
        "task_id": task_id,
        "phone": phone,
        "sms_count": sms_count,
        "call_count": call_count
    })

@app.route("/status/<task_id>")
def get_status(task_id):
    return jsonify({
        "task_id": task_id,
        "status": active_tasks.get(task_id, "Not Found")
    })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        threaded=True
    )