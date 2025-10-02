import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import datetime
import psycopg2




# Add at the top
from flask import Flask
from threading import Thread

app = Flask("ping_server")

# Health check route
@app.route("/health")
def health():
    return "I'm alive!", 200

# Function to run Flask server
def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# Start Flask server in separate thread
Thread(target=run).start()





# Load token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8289675906:AAGNbSgd2mk_KtNLYUriVxBVR-7CgwU5ZYA")
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
    protein DOUBLE PRECISION,
    gram DOUBLE PRECISION
);
""")
conn.commit()


#orakani hamar

cursor.execute("""
CREATE TABLE IF NOT EXISTS userday (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    kkal DOUBLE PRECISION,
    protein DOUBLE PRECISION
);
""")
conn.commit()

#newdaily

cursor.execute("""
CREATE TABLE IF NOT EXISTS daily (
    id SERIAL PRIMARY KEY,
    kkal DOUBLE PRECISION DEFAULT 2200,
    protein DOUBLE PRECISION DEFAULT 110
);
""")

cursor.execute("""
INSERT INTO daily (kkal, protein)
SELECT 2200, 110
WHERE NOT EXISTS (SELECT 1 FROM daily)
""")

conn.commit()

def newdaily(kkal,protein):
    cursor.execute("UPDATE daily SET kkal=%s, protein=%s", (kkal, protein))

    conn.commit()
    return f"now Your Daily id {kkal}calories and {protein}protein"

def getdaily():
    cursor.execute("SELECT * FROM daily")
    return cursor.fetchone()

def update_daily(kkal, protein):
    today = datetime.date.today()
    date_str = today.strftime("%d/%m/%Y")

    # Check if a row already exists for today
    cursor.execute("SELECT kkal, protein FROM userday WHERE date=%s", (date_str,))
    row = cursor.fetchone()

    if row:
        # Add to existing values
        old_kkal, old_protein = row
        new_kkal = old_kkal + kkal
        new_protein = old_protein + protein
        cursor.execute("UPDATE userday SET kkal=%s, protein=%s WHERE date=%s",
                       (new_kkal, new_protein, date_str))
        conn.commit()
        return [new_kkal,new_protein]
    else:
        # Create new row
        cursor.execute("INSERT INTO userday (date, kkal, protein) VALUES (%s, %s, %s)",
                       (date_str, kkal, protein))
        conn.commit()
        return [kkal, protein]

def add_product(name, kkal, protein, gram):
    cursor.execute("INSERT INTO products (name, kkal, protein, gram) VALUES (%s, %s, %s, %s)",
                   (name, kkal, protein, gram))
    conn.commit()

def get_products():
    cursor.execute("SELECT * FROM products")
    return cursor.fetchall()

def update_product(name, new_kkal, new_protein, new_gram):
    cursor.execute("UPDATE products SET kkal=%s, protein=%s, gram=%s WHERE name=%s",
                   (new_kkal, new_protein, new_gram, name))
    conn.commit()

def get_product_by_id(pid):
    cursor.execute("SELECT * FROM products WHERE id=%s", (pid,))
    return cursor.fetchone()

def delete_product(name):
    try:
        cursor.execute("DELETE FROM products WHERE name=%s", (name,))
        conn.commit()
        print(f'Deleted {name}')
        return f"{name} was deleted from db"
    except:
        return "something went wrong maybe you havent this in your db"

def get_product_by_name(name):
    cursor.execute("SELECT * FROM products WHERE name ILIKE %s", (f"%{name}%",))

    return cursor.fetchone()


# --- FSM States ---
class AddProduct(StatesGroup):
    waiting_for_data = State()

class UpdateProduct(StatesGroup):
    waiting_for_data = State()

# --- /start ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Hi! You can use commands:\n- add\n- update\n- show")

# --- Echo handler ---
@dp.message()
async def echo_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()

    # ------------------- ADD -------------------
    if text.lower() == "add":
        await message.answer("Enter product as: name kkal protein gram")
        await state.set_state(AddProduct.waiting_for_data)
        return

    if await state.get_state() == AddProduct.waiting_for_data:
        parts = text.split()
        if len(parts) != 4:
            await message.answer("❌ Wrong format. Use: name kkal protein gram")
            return
        name, kkal, protein, gram = parts
        if gram.endswith('g'):
            gram=gram[:-1]
        add_product(name, float(kkal), float(protein), float(gram))
        await message.answer(f"✅ Added: {name} ({kkal} kcal, {protein} protein, {gram} g)")
        await state.clear()
        return

    if text.lower().startswith("add"):
        parts = text[3:].split()
        if len(parts) != 4:
            await message.answer("❌ Wrong format. Use: add name kkal protein gram")
            return
        name, kkal, protein, gram = parts
        if gram.endswith('g'):
            gram=gram[:-1]
        add_product(name, float(kkal), float(protein), float(gram))
        await message.answer(f"✅ Added: {name} ({kkal} kcal, {protein} protein, {gram} g)")
        return

    # ------------------- UPDATE -------------------
    if text.lower() == "update":
        await message.answer("Enter product update as: name kkal protein gram")
        await state.set_state(UpdateProduct.waiting_for_data)
        return

    if await state.get_state() == UpdateProduct.waiting_for_data:
        parts = text.split()
        if len(parts) != 4:
            await message.answer("❌ Wrong format. Use: name kkal protein gram")
            return
        name, kkal, protein, gram = parts
        update_product(name, float(kkal), float(protein), float(gram))
        await message.answer(f"♻️ Updated: {name} → {kkal}/{protein}/{gram}")
        await state.clear()
        return

    if text.lower().startswith("update"):
        parts = text[6:].split()
        if len(parts) != 4:
            await message.answer("❌ Wrong format. Use: update name kkal protein gram")
            return
        name, kkal, protein, gram = parts
        if gram.endswith('g'):
            gram=gram[:-1]
        update_product(name, float(kkal), float(protein), float(gram))
        await message.answer(f"♻️ Updated: {name} → {kkal}/{protein}/{gram}")
        return

    # ------------------- SHOW -------------------
    if text.lower() == "show":
        products = get_products()
        if not products:
            await message.answer("📭 No products found.")
            return

        message_text = "📦 Products:\n\n"
        for _, name, kkal, protein, gram in products:
            message_text += f"•{name} | {kkal} kcal | {protein} p | {gram} g\n"

        await message.answer(message_text)
        return

    if text.lower().startswith("delete"):
        parts = text[6:].split()
        name=parts[0]
        print(parts)
        await message.answer(delete_product(name))
        return

    # ------------------- Set Daily -------------------

    if text.lower().startswith("setday"):
        parts = text[6:].split()
        kkal,protein=parts
        await message.answer(newdaily(kkal,protein))
        return



    #/sovorakan

    # Check if user wants to calculate calories/protein
    parts = text.split()
    if len(parts) >= 1:
        print('1')
        prod_name = parts[0]
        product = get_product_by_name(prod_name)
        if product:
            _, name, kkal, protein, db_gram = product

            # Check if user provided a custom gram
            if len(parts) == 2 :
                try:
                    gram = float(parts[1])  # remove 'g' and convert
                except ValueError:
                    gram = float(parts[1][:-1])
            else:
                gram = db_gram

            calc_kcal = kkal * gram / 100
            calc_protein = protein * gram / 100
            kk,pp=update_daily(calc_kcal,calc_protein)
            _,dk,dpp=getdaily()
            await message.answer(
                f"📌 *{name}*\n"
                f"🔥 Calories: {calc_kcal:.1f} kcal\n"
                f"🥩 Protein: {calc_protein:.1f} g\n"
                f"⚖️ Weight: {gram} g",
                parse_mode="Markdown"
            )
            await message.answer(
                f"📌 Your Daily is {dk} and{dpp}\n"
                f"Now 🔥 Calories: {kk:.1f} kcal\n"
                f"Now 🥩 Protein: {pp:.1f} g\n"
                f"Have to Eat {int(round(dk-kk))} kcal and {int(round(dpp-pp))} protein\n",
                parse_mode="Markdown"
            )
            return
    # Default echo
    print(f"[{message.from_user.username}] {text}")
    await message.answer(f"You said: {text}")



# --- Run bot ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
