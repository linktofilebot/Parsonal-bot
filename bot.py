import os
import subprocess
import sys

# --- ১. অটো লাইব্রেরি ইন্সটলেশন ---
def install_requirements():
    requirements = ['pyTelegramBotAPI', 'pymongo', 'requests', 'dnspython']
    for lib in requirements:
        try:
            __import__(lib if lib != 'pyTelegramBotAPI' else 'telebot')
        except ImportError:
            print(f"Installing {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

install_requirements()

import telebot
import requests
import pymongo
from telebot import types

# --- ২. কনফিগারেশন ---
BOT_TOKEN = '8348660690:AAH84DwkNBfUOqoWcl3s2tRartTQZFqm4I0' 
MONGO_URL = 'mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

try:
    client = pymongo.MongoClient(MONGO_URL)
    db = client['ProMovieBot_Final']
    config_col = db['user_configs']
    print("✅ MongoDB Connected Successfully!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    sys.exit()

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

# ডাটাবেস ফাংশন
def get_settings(user_id):
    data = config_col.find_one({"user_id": user_id})
    if not data:
        default = {
            "user_id": user_id,
            "lang": "Hindi Dubbed",
            "eps": "Full Movie / All Episodes",
            "dl_guide": "https://t.me/BotFileD/3",
            "share_link": "https://t.me/+OnHo082TYJ5lZGU1",
            "backup_link": "https://t.me/+cv6z0wFhgq45ZWFl",
            "api_key": "None",
            "shortener_url": "https://gplinks.in/api",
            "api_param": "api", # কাস্টম প্যারামিটার ১
            "url_param": "url", # কাস্টম প্যারামিটার ২
            "channels": []
        }
        config_col.insert_one(default)
        return default
    return data

# --- ৩. কিবোর্ড মেনু ---

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🆕 Create Post", "📋 My Settings")
    markup.row("⚙️ Setup Bot", "📢 Manage Channels")
    markup.row("📖 Help")
    return markup

def setup_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔊 Language", callback_data="set_lang"),
        types.InlineKeyboardButton("💿 Episodes", callback_data="set_eps"),
        types.InlineKeyboardButton("🔑 API Key", callback_data="set_api"),
        types.InlineKeyboardButton("🔗 API URL", callback_data="set_url"),
        types.InlineKeyboardButton("🆔 Key Parameter", callback_data="set_param_key"),
        types.InlineKeyboardButton("🆔 URL Parameter", callback_data="set_param_url"),
        types.InlineKeyboardButton("📥 Guide Link", callback_data="set_guide"),
        types.InlineKeyboardButton("🔞 Backup Link", callback_data="set_backup"),
        types.InlineKeyboardButton("🔗 Share Link", callback_data="set_share")
    )
    return markup

def channels_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ Add Channel", callback_data="add_ch"),
        types.InlineKeyboardButton("🗑 Delete Channel", callback_data="del_ch"),
        types.InlineKeyboardButton("📜 My Channels", callback_data="view_ch")
    )
    return markup

# --- ৪. ১০০% ডাইনামিক শর্টনার ইঞ্জিন ---
def get_short_link(long_url, s):
    if s['api_key'] == "None" or not s['api_key']:
        return long_url
    try:
        api_url = s['shortener_url'].strip()
        # ইউজারের কাস্টম প্যারামিটার অনুযায়ী রিকোয়েস্ট তৈরি করা
        params = {
            s.get('api_param', 'api'): s['api_key'],
            s.get('url_param', 'url'): long_url
        }
        res = requests.get(api_url, params=params, timeout=15)
        
        if res.status_code == 200:
            try:
                data = res.json()
                # যেকোনো কি-নাম থেকে অটো লিঙ্ক খুঁজে বের করার স্মার্ট লজিক
                for key in ['shortenedUrl', 'url', 'short_url', 'link', 'shortlink', 'data']:
                    if key in data:
                        if isinstance(data[key], str): return data[key]
                        elif isinstance(data[key], dict) and 'url' in data[key]: return data[key]['url']
                return res.text.strip() if "http" in res.text else long_url
            except:
                return res.text.strip() if "http" in res.text else long_url
        return long_url
    except:
        return long_url

# --- ৫. মেসেজ হ্যান্ডলারস ---

@bot.message_handler(commands=['start'])
def start_bot(message):
    get_settings(message.chat.id)
    bot.send_message(
        message.chat.id, 
        "<b>🚀 মুভি পোস্ট মেকার প্রো-তে স্বাগতম!</b>",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda message: True)
def handle_reply_buttons(message):
    user_id = message.chat.id
    if message.text == "🆕 Create Post":
        msg = bot.send_message(user_id, "<b>🖼 মুভির ছবি বা পোস্টার পাঠান:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, step_1_receive_logo)

    elif message.text == "📋 My Settings":
        s = get_settings(user_id)
        info = (f"<b>📊 বর্তমান সেটিংস:</b>\n\n"
                f"<b>🔊 ভাষা: {s['lang']}</b>\n"
                f"<b>💿 এপিসোড: {s['eps']}</b>\n"
                f"<b>🔗 API URL: {s['shortener_url']}</b>\n"
                f"<b>🔑 API Key: {s['api_key']}</b>\n"
                f"<b>🆔 Key Param: {s.get('api_param', 'api')}</b>\n"
                f"<b>🆔 URL Param: {s.get('url_param', 'url')}</b>\n"
                f"<b>📢 মোট চ্যানেল: {len(s['channels'])} টি</b>")
        bot.send_message(user_id, info, parse_mode="HTML")

    elif message.text == "⚙️ Setup Bot":
        bot.send_message(user_id, "<b>⚙️ কি পরিবর্তন করতে চান?</b>", reply_markup=setup_inline(), parse_mode="HTML")

    elif message.text == "📢 Manage Channels":
        bot.send_message(user_id, "<b>📢 চ্যানেল কন্ট্রোল মেনু:</b>", reply_markup=channels_keyboard(), parse_mode="HTML")

# --- ৬. পোস্ট তৈরির প্রসেস (বোল্ড ডিজাইন) ---

def step_1_receive_logo(message):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "<b>❌ ছবি পাঠান!</b>", parse_mode="HTML")
        return
    user_states[message.chat.id] = {'photo_id': message.photo[-1].file_id}
    msg = bot.send_message(message.chat.id, "<b>📝 মুভির নাম লিখে পাঠান:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_2_receive_name)

def step_2_receive_name(message):
    user_states[message.chat.id]['movie_name'] = message.text.upper()
    msg = bot.send_message(message.chat.id, "<b>🔗 মুভির মেইন লিঙ্ক পাঠান:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_3_final_process)

def step_3_final_process(message):
    user_id = message.chat.id
    main_url = message.text
    data = user_states.get(user_id)
    s = get_settings(user_id)

    if not data: return

    wait = bot.send_message(user_id, "<b>⏳ প্রসেসিং...</b>", parse_mode="HTML")
    short_link = get_short_link(main_url, s)

    # সম্পুর্ন বোল্ড ডিজাইন
    post_design = f"""
<b>╔════════════════════════╗</b>
<b>          ✨ {data['movie_name']} ✨</b>
<b>╚════════════════════════╝</b>

<b>🎬 Drama Name : {data['movie_name']}</b>
<b>🔊 Language   : {s['lang']}</b>
<b>💿 Episodes   : {s['eps']}</b>

<b>📥 Watch / Download Link:</b>
<b>🔗 {short_link}</b>

<b>📥 How to Download:</b>
<b>🔗 {s['dl_guide']}</b>

<b>📢 Share Channel:</b>
<b>🔗 {s['share_link']}</b>

<b>🔞 Join Our Backup Channel:</b>
<b>🔗 {s['backup_link']}</b>

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>   🍿 ENJOY YOUR DRAMA 🍿</b>
    """

    bot.send_photo(user_id, data['photo_id'], caption=post_design, parse_mode='HTML')

    success = 0
    for ch in s['channels']:
        try:
            bot.send_photo(ch, data['photo_id'], caption=post_design, parse_mode='HTML')
            success += 1
        except: pass

    bot.delete_message(user_id, wait.message_id)
    bot.send_message(user_id, f"<b>✅ সফলভাবে {success}টি চ্যানেলে পাঠানো হয়েছে!</b>", reply_markup=main_keyboard(), parse_mode="HTML")
    user_states.pop(user_id, None)

# --- ৭. কলব্যাক এবং আপডেট ---

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.message.chat.id
    fields = {
        "set_lang": "lang", "set_eps": "eps", "set_api": "api_key",
        "set_url": "shortener_url", "set_guide": "dl_guide",
        "set_backup": "backup_link", "set_share": "share_link",
        "set_param_key": "api_param", "set_param_url": "url_param"
    }
    
    if call.data in fields:
        msg = bot.send_message(user_id, "<b>📥 নতুন তথ্যটি লিখে পাঠান:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, update_db, fields[call.data])
    
    elif call.data == "view_ch":
        s = get_settings(user_id)
        if s['channels']:
            ch_list = "\n".join([f"<b>🔹 {c}</b>" for c in s['channels']])
            bot.send_message(user_id, f"<b>📢 চ্যানেলসমূহ:</b>\n\n{ch_list}", parse_mode="HTML")
        else:
            bot.send_message(user_id, "<b>❌ কোনো চ্যানেল নেই</b>", parse_mode="HTML")
    
    elif call.data == "add_ch":
        msg = bot.send_message(user_id, "<b>📥 চ্যানেলের @Username দিন:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, add_ch)
    
    elif call.data == "del_ch":
        msg = bot.send_message(user_id, "<b>🗑 ডিলিট করতে চ্যানেলের @Username দিন:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, del_ch)
    
    bot.answer_callback_query(call.id)

def update_db(message, field):
    config_col.update_one({"user_id": message.chat.id}, {"$set": {field: message.text}})
    bot.send_message(message.chat.id, "<b>✅ তথ্য সেভ হয়েছে!</b>", parse_mode="HTML")

def add_ch(message):
    name = message.text.strip()
    config_col.update_one({"user_id": message.chat.id}, {"$addToSet": {"channels": name}})
    bot.send_message(message.chat.id, f"<b>✅ {name} যুক্ত হয়েছে।</b>", parse_mode="HTML")

def del_ch(message):
    name = message.text.strip()
    config_col.update_one({"user_id": message.chat.id}, {"$pull": {"channels": name}})
    bot.send_message(message.chat.id, f"<b>🗑 {name} ডিলিট হয়েছে।</b>", parse_mode="HTML")

if __name__ == '__main__':
    print("🤖 Bot is starting...")
    bot.infinity_polling()
