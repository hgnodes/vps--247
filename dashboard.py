from fastapi import FastAPI
from typing import List
import time

app = FastAPI()
STATUS = {}

@app.get("/")
def home():
    return {
        "service": "IDX Monitor",
        "active": len(STATUS),
        "time": time.time()
    }

@app.get("/status")
def status():
    return STATUS

def update_status(ip, online):
    STATUS[ip] = {
        "online": online,
        "last_check": time.time()
    }
