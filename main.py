import telebot
from telebot import types
import sqlite3
import random
import string
from PIL import Image, ImageDraw, ImageFont
import io
import os
import tempfile
from datetime import datetime
import pandas as pd

# Bot tokeningizni kiriting
TOKEN = '7293612246:AAFTItrVlDoRsWn8w5mGNEvwjWRU2OcuHXA'
bot = telebot.TeleBot(TOKEN)

# Adminning telefon raqami yoki user ID'sini kiriting
ADMIN_ID = '7013844896'

# Ma'lumotlar bazasiga ulanish
conn = sqlite3.connect('participants.db', check_same_thread=False)
cursor = conn.cursor()


import sqlite3

import sqlite3

# Ma'lumotlar bazasiga ulanish
conn = sqlite3.connect('participants.db', check_same_thread=False)
cursor = conn.cursor()

# Jadvalni yaratish
cursor.execute("""CREATE TABLE IF NOT EXISTS S (
    participant_number INTEGER PRIMARY KEY,
    is_active INTEGER DEFAULT 0
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_number INTEGER,
    user_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    verified INTEGER DEFAULT 0
);""")

# Ustun qo'shish
try:
    cursor.execute("ALTER TABLE votes ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;")
except sqlite3.OperationalError:
    pass  # Agar ustun allaqon mavjud bo'lsa, hech narsa qilmaymiz

conn.commit()





# Global o'zgaruvchi - ovoz berish jarayoni holati
voting_active = False

# Admin uchun tugmalar interfeysi
def admin_commands_keyboard():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton('End'), types.KeyboardButton('Result'))
    markup.add(types.KeyboardButton('Start'), types.KeyboardButton('Stop'))
    markup.add(types.KeyboardButton('Create'), types.KeyboardButton('About'))  # "About" tugmasini qo'shish
    markup.add(types.KeyboardButton('Export Results'))  # Excelga natijalarni eksport qilish tugmasi
    return markup


# Admin buyruqlari uchun handlerlar
@bot.message_handler(func=lambda message: str(message.chat.id) == ADMIN_ID and message.text in ['End', 'Result', 'Start', 'Stop', 'Create', 'About', 'Export Results'])
def admin_commands(message):
    global voting_active
    if message.text == 'End':
        # Barcha jadvallarni tozalash
        cursor.execute("DELETE FROM S")
        cursor.execute("DELETE FROM votes")
        cursor.execute("DELETE FROM users")
        conn.commit()
        bot.send_message(message.chat.id, "Barcha ma'lumotlar tozalandi!")
    elif message.text == 'Result':
        cursor.execute("SELECT participant_number, COUNT(*) FROM votes GROUP BY participant_number")
        results = cursor.fetchall()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if results:
            result_message = f"Ovozlar natijalari (yangilangan vaqt: {current_time}):\n"
            for participant in results:
                result_message += f"Ishtirokchi {participant[0]}: {participant[1]} ovoz\n"
            bot.send_message(message.chat.id, result_message)
        else:
            bot.send_message(message.chat.id, f"Hech kim ovoz bermagan (yangilangan vaqt: {current_time}).")
    elif message.text == 'Start':
        voting_active = True
        cursor.execute("UPDATE S SET is_active = 1")
        conn.commit()
        bot.send_message(message.chat.id, "Ovoz berish jarayoni boshlandi!")
    elif message.text == 'Stop':
        voting_active = False
        cursor.execute("UPDATE S SET is_active = 0")
        conn.commit()
        bot.send_message(message.chat.id, "Ovoz berish jarayoni to'xtatildi!")
    elif message.text == 'Create':
        cursor.execute("SELECT COUNT(*) FROM S")
        participant_count = cursor.fetchone()[0]

        if participant_count > 0:
            bot.send_message(message.chat.id, "So'rovnoma allaqachon yaratilgan.")
        else:
            bot.send_message(message.chat.id, "Ishtirokchilar sonini kiriting:")
            bot.register_next_step_handler(message, save_participants)
    elif message.text == 'About':
        about_message = "Bu bot ishtirokchilarga ovoz berish imkoniyatini beradi. Ovoz berish jarayoni admin tomonidan boshqariladi."
        bot.send_message(message.chat.id, about_message)
    elif message.text == 'Export Results':
        cursor.execute(""" 
                    SELECT v.participant_number, v.user_id 
                    FROM votes v 
                    """)
        results = cursor.fetchall()

        if results:
            df = pd.DataFrame(results,
                              columns=["Ishtirokchi raqami", "Foydalanuvchi ID"])
            excel_file = "voting_results.xlsx"
            df.to_excel(excel_file, index=False)

            with open(excel_file, 'rb') as file:
                bot.send_document(message.chat.id, file)

            bot.send_message(message.chat.id, "Natijalar Excel fayli sifatida yuborildi.")
        else:
            bot.send_message(message.chat.id, "Hech kim ovoz bermagan.")

    # Tugmalarni qayta ko'rsatish
    bot.send_message(message.chat.id, "Buyruq tugmalari:", reply_markup=admin_commands_keyboard())

# Kiritilgan ishtirokchilar soni asosida bazaga qo'shish
def save_participants(message):
    try:
        participants_number = int(message.text)
        cursor.execute("DELETE FROM S")  # Oldingi ishtirokchilarni o'chirish
        for i in range(1, participants_number + 1):
            cursor.execute("INSERT INTO S (participant_number) VALUES (?)", (i,))
        conn.commit()
        bot.send_message(message.chat.id, f"{participants_number} ishtirokchi bazaga qo'shildi.")
    except ValueError:
        bot.send_message(message.chat.id, "Iltimos, to'g'ri son kiriting.")


@bot.message_handler(commands=['start'])
def start_command(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "Salom, admin!", reply_markup=admin_commands_keyboard())
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        channel_button = telebot.types.InlineKeyboardButton("Telegram kanaliga a'zo bo'lish", url="https://t.me/mono_electric_uz")
        group_button = telebot.types.InlineKeyboardButton("Telegram guruhiga a'zo bo'lish", url="https://t.me/mono_electric_chat")
        instagram_button = telebot.types.InlineKeyboardButton("Instagram sahifasiga a'zo bo'lish", url="https://www.instagram.com/mono.electric.uz")
        check_button = telebot.types.InlineKeyboardButton("Tekshirish", callback_data="check_subscriptions")
        result_button = telebot.types.KeyboardButton("Natija")
        markup.add(channel_button, group_button, instagram_button, check_button)

        bot.send_message(message.chat.id, "Iltimos, quyidagi Telegram va Instagram tarmoqlariga a'zo bo'ling va keyin tekshirish tugmasini bosing:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscriptions")
def check_subscriptions(call):
    bot.answer_callback_query(call.id, "Tekshirish amalga oshirildi. Iltimos, o'z telefon raqamingizni yuboring:")
    bot.send_message(call.message.chat.id, "Iltimos, o'z telefon raqamingizni yuboring:", reply_markup=telebot.types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True).add(telebot.types.KeyboardButton("📞 Raqamni jo'natish", request_contact=True)))

def generate_captcha(text):
    # Rasm o'lchamlari
    width, height = 200, 100
    # Rasm yaratish
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Font o'rnatish (standart fontni ishlatish)
    font = ImageFont.load_default()

    # Rasmga matn qo'shish
    text_bbox = draw.textbbox((0, 0), text, font=font)  # Text bounding box
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    draw.text(((width - text_width) / 2, (height - text_height) / 2), text, fill=(0, 0, 0), font=font)

    # Faqat tasodifiy nuqtalar qo'shish
    for _ in range(random.randint(50, 100)):  # 50-100 tasodifiy nuqta
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(0, 0, 0))

    return image, text


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    captcha_text = ''.join(random.choices(string.digits, k=4))
    captcha_image, correct_answer = generate_captcha(captcha_text)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        captcha_image.save(tmp_file, format='PNG')
        tmp_file_path = tmp_file.name

    with open(tmp_file_path, 'rb') as photo:
        bot.send_photo(message.chat.id, photo, caption="Iltimos, yuqoridagi raqamlarni kiriting:")

    os.remove(tmp_file_path)

    bot.register_next_step_handler(message, lambda m: check_captcha_answer(m, correct_answer))


def check_captcha_answer(message, correct_answer):
    user_id = message.from_user.id

    # Telefon raqamini olish
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        phone_number = "unknown"

    if message.text == correct_answer:
        bot.send_message(message.chat.id, "Siz muvaffaqiyatli tasdiqladingiz!")

        # Telefon raqamini saqlash
        cursor.execute("INSERT OR REPLACE INTO users (user_id, phone_number, verified) VALUES (?, ?, ?)",
                       (user_id, phone_number, 1))
        conn.commit()

        # Tugmalarni ko'rsatish
        show_main_buttons(message.chat.id)
    else:
        bot.send_message(message.chat.id, "CAPTCHA noto'g'ri, iltimos, qayta urinib ko'ring.")
        contact_handler(message)


def show_main_buttons(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    result_button = telebot.types.KeyboardButton("Natija")

    markup.add(result_button)
    bot.send_message(chat_id, "Natija berish tugmalarini bosing:", reply_markup=markup)

    # Ishtirokchilarni ko'rsatish
    show_participants_inline(chat_id)  # Ishtirokchilar ro'yxatini ko'rsatish


def show_participants_inline(chat_id):
    cursor.execute("SELECT participant_number FROM S WHERE is_active = 1")
    participants = cursor.fetchall()

    if participants:
        markup = telebot.types.InlineKeyboardMarkup()
        for participant in participants:
            participant_number = participant[0]
            markup.add(types.InlineKeyboardButton(f"{participant_number} - Ishtirokchiga ovoz berish", callback_data=f"vote_{participant_number}"))

        bot.send_message(chat_id, "Iltimos, ishtirokchilardan biriga ovoz bering:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Hozirda ishtirokchilar mavjud emas.")



@bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
def handle_vote(call):
    participant_number = call.data.split("_")[1]

    local_cursor = conn.cursor()

    try:
        # Foydalanuvchini tekshirish
        local_cursor.execute("SELECT * FROM users WHERE user_id = ?", (call.from_user.id,))
        user = local_cursor.fetchone()

        if user:
            # Foydalanuvchining oldin ovoz berganligini tekshirish
            local_cursor.execute("SELECT * FROM votes WHERE user_id = ?", (call.from_user.id,))
            existing_votes = local_cursor.fetchall()

            # Agar foydalanuvchi allaqachon ovoz bergan bo'lsa
            if existing_votes:
                bot.answer_callback_query(call.id, "Siz allaqachon ovoz bergansiz! Faqat bitta ovoz berishingiz mumkin.")
            else:
                # Ovoz berish
                local_cursor.execute("INSERT INTO votes (participant_number, user_id, phone_number) VALUES (?, ?, ?)",
                                     (participant_number, call.from_user.id, user[1]))  # user[1] - phone_number
                conn.commit()
                bot.answer_callback_query(call.id, f"Siz {participant_number} ishtirokchisiga ovoz berdingiz!")
        else:
            bot.answer_callback_query(call.id, "Siz ovoz berish uchun tasdiqlanmagan ekansiz.")
    finally:
        local_cursor.close()



@bot.message_handler(func=lambda message: message.text == "Natija")
def handle_results(message):
    cursor.execute("SELECT participant_number, COUNT(*) FROM votes GROUP BY participant_number")
    results = cursor.fetchall()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Hozirgi vaqtni olish

    if results:
        result_message = f"Ovozlar natijalari (yangilangan vaqt: {current_time}):\n"
        for participant in results:
            result_message += f"Ishtirokchi {participant[0]}: {participant[1]} ovoz\n"
        bot.send_message(message.chat.id, result_message)
    else:
        bot.send_message(message.chat.id, f"Hech kim ovoz bermagan (yangilangan vaqt: {current_time}).")


@bot.message_handler(func=lambda message: voting_active)
def vote(message):
    phone_number = message.text  # Telefon raqamini olish
    user_id = message.from_user.id

    # Foydalanuvchini ro'yxatdan o'tkazish
    cursor.execute("INSERT OR IGNORE INTO users (user_id, phone_number) VALUES (?, ?)", (user_id, phone_number))

    # Ovoz berish
    participant_number = ...  # Ovoz berilayotgan ishtirokchi raqamini aniqlang
    cursor.execute("INSERT INTO votes (participant_number, user_id, phone_number) VALUES (?, ?, ?)",
                   (participant_number, user_id, phone_number))
    conn.commit()
    bot.send_message(message.chat.id, "Sizning ovozingiz qabul qilindi!")


# Botni ishga tushirish
bot.polling(none_stop=True)
