# src/client.py

import requests
import time

# URLs for each node
nodes = {
    "node1": "http://localhost:5001",
    "node2": "http://localhost:5002",
    "node3": "http://localhost:5003"
}

def print_read(node, key):
    response = requests.get(f"{nodes[node]}/read", params={"key": key})
    print(f"Read from {node}: {response.json()}")

def write(node, key, value):
    response = requests.post(f"{nodes[node]}/write", json={"key": key, "value": value})
    print(f"Write to {node}: {response.json()}")

def main():
    print("\n--- Step 1: Write x=5 to node1 ---")
    write("node1", "x", 5)

    time.sleep(2)

    print("\n--- Step 2: Read x from node2 (simulate causal dependency) ---")
    print_read("node2", "x")

    print("\n--- Step 3: Update x=10 to node3 (depends on previous value) ---")
    write("node3", "x", 10)

    time.sleep(3)

    print("\n--- Final Reads ---")
    print_read("node1", "x")
    print_read("node2", "x")
    print_read("node3", "x")

if __name__ == "__main__":
    main()
