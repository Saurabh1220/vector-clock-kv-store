# src/node.py

from flask import Flask, request, jsonify
import requests
import threading
import time
import os

app = Flask(__name__)

# Unique ID for this node (passed via environment variable)
NODE_ID = os.getenv("NODE_ID", "node1")

# Comma-separated list of peer hostnames (passed via env variable)
PEERS = os.getenv("PEERS", "").split(",")

# Initialize vector clock
vector_clock = {}
store = {}
buffer = []

def init_clock():
    for peer in PEERS + [NODE_ID]:
        if peer:
            vector_clock[peer] = 0

def increment_clock():
    vector_clock[NODE_ID] += 1

def merge_clock(received):
    for node, val in received.items():
        vector_clock[node] = max(vector_clock.get(node, 0), val)

def can_deliver(received, sender):
    for node in vector_clock:
        if node == sender:
            if received[node] != vector_clock[node] + 1:
                return False
        else:
            if received[node] > vector_clock[node]:
                return False
    return True

def try_deliver_buffer():
    for msg in buffer[:]:
        if can_deliver(msg["clock"], msg["sender"]):
            store[msg["key"]] = msg["value"]
            merge_clock(msg["clock"])
            buffer.remove(msg)

@app.route("/write", methods=["POST"])
def write():
    data = request.json
    key = data["key"]
    value = data["value"]

    increment_clock()
    store[key] = value

    message = {
        "key": key,
        "value": value,
        "clock": vector_clock.copy(),
        "sender": NODE_ID
    }

    # Send to peers
    for peer in PEERS:
        if peer:
            try:
                requests.post(f"http://{peer}:5000/replicate", json=message, timeout=1)
            except Exception as e:
                print(f"Replication to {peer} failed: {e}")

    return jsonify({
        "status": "written",
        "clock": vector_clock,
        "store": store
    })

@app.route("/replicate", methods=["POST"])
def replicate():
    data = request.json
    key = data["key"]
    value = data["value"]
    clock = data["clock"]
    sender = data["sender"]

    if can_deliver(clock, sender):
        print(f"[{NODE_ID}] DELIVERED: {key}={value} from {sender} with clock {clock}")
        store[key] = value
        merge_clock(clock)
        try_deliver_buffer()
        return jsonify({"status": "delivered"})
    else:
        print(f"[{NODE_ID}] BUFFERED: {key}={value} from {sender} with clock {clock}")
        buffer.append({
            "key": key,
            "value": value,
            "clock": clock,
            "sender": sender
        })
        return jsonify({"status": "buffered"})

@app.route("/read", methods=["GET"])
def read():
    key = request.args.get("key")
    return jsonify({
        "key": key,
        "value": store.get(key),
        "clock": vector_clock
    })

# Background thread to periodically try buffer
def buffer_check_loop():
    while True:
        try_deliver_buffer()
        time.sleep(1)

if __name__ == "__main__":
    init_clock()
    threading.Thread(target=buffer_check_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
