import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import datetime
import psycopg2



from flask import Flask
from threading import Thread
import threading, time, requests, os

app = Flask("ping_server")

# Health check route
@app.route("/", methods=["GET", "HEAD"])
def health():
    return "I'm alive!", 200

# Function to run Flask server
def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# Keep-alive function
def keep_alive():
    url = "https://4faa165f-a2bd-4db7-96ee-69834ba3d9f5-00-z4iumwxv3mvu.sisko.replit.dev/"
    while True:
        try:
            r = requests.get(url)
            print("Self-ping:", r.status_code)
        except Exception as e:
            print("Self-ping failed:", e)
        time.sleep(60)  # every 1 minute

# Start both threads
if __name__ == "__main__":
    Thread(target=run).start()
    Thread(target=keep_alive, daemon=True).start()





# Load token
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- DB setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    kkal DOUBLE PRECISION,
