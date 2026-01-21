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

# --- ২. কনফিগারেশন (Configuration) ---
BOT_TOKEN = '8348660690:AAFdZ11IxHSeX5NVFqOWnkXfSlRbTqDZ32I' 
MONGO_URL = 'mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

# --- ৩. ডাটাবেস কানেকশন ---
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

# ডাটাবেস থেকে সেটিংস লোড/তৈরি
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
            "channels": []
        }
        config_col.insert_one(default)
        return default
    return data

# --- ৪. কিবোর্ড মেনু (Keyboards) ---

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

# --- ৫. ১০০% ইউনিভার্সাল লিঙ্ক শর্টনার লজিক ---
def get_short_link(long_url, api_key, api_url):
    if api_key == "None" or not api_key or not api_url:
        return long_url
    try:
        # লিঙ্ক তৈরি (সব শর্টনারের কমন মেথড)
        base_url = api_url.strip()
        params = {'api': api_key, 'url': long_url}
        
        # কিছু শর্টনারে 'api' এর বদলে 'token' বা 'key' ব্যবহার হয়, তবে ৯৯% ই 'api' নেয়।
        res = requests.get(base_url, params=params, timeout=15)
        
        if res.status_code == 200:
            try:
                data = res.json()
                # শর্টনার থেকে আসা ডাটা থেকে স্মার্টলি লিঙ্ক খোঁজা
                possible_keys = ['shortenedUrl', 'url', 'short_url', 'link', 'shortlink', 'data']
                for key in possible_keys:
                    if key in data:
                        if isinstance(data[key], str):
                            return data[key]
                        elif isinstance(data[key], dict) and 'url' in data[key]:
                            return data[key]['url']
                # যদি JSON এর ভেতর না পায় তবে টেক্সট চেক করবে
                return res.text.strip() if "http" in res.text else long_url
            except:
                return res.text.strip() if "http" in res.text else long_url
        return long_url
    except:
        return long_url

# --- ৬. মেইন মেসেজ হ্যান্ডলারস ---

@bot.message_handler(commands=['start'])
def start_bot(message):
    get_settings(message.chat.id)
    bot.send_message(
        message.chat.id, 
        "<b>🚀 মুভি পোস্ট মেকার প্রলু ভার্সনে স্বাগতম!</b>\n\n<b>নিচের বাটনগুলো ব্যবহার করে কাজ শুরু করুন।</b>",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda message: True)
def handle_reply_buttons(message):
    user_id = message.chat.id
    if message.text == "🆕 Create Post":
        msg = bot.send_message(user_id, "<b>🖼 প্রথমে মুভির লগো বা পোস্টার (ছবি) পাঠান:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, step_1_receive_logo)

    elif message.text == "📋 My Settings":
        s = get_settings(user_id)
        info = (f"<b>📊 আপনার বর্তমান সেটিংস:</b>\n\n"
                f"<b>🔊 ভাষা: {s['lang']}</b>\n"
                f"<b>💿 এপিসোড: {s['eps']}</b>\n"
                f"<b>🔗 API URL: {s['shortener_url']}</b>\n"
                f"<b>🔑 API Key: {s['api_key']}</b>\n"
                f"<b>📢 মোট চ্যানেল: {len(s['channels'])} টি</b>")
        bot.send_message(user_id, info, reply_markup=main_keyboard(), parse_mode="HTML")

    elif message.text == "⚙️ Setup Bot":
        bot.send_message(user_id, "<b>⚙️ কোন তথ্যটি পরিবর্তন করতে চান?</b>", reply_markup=setup_inline(), parse_mode="HTML")

    elif message.text == "📢 Manage Channels":
        bot.send_message(user_id, "<b>📢 চ্যানেল ম্যানেজমেন্ট মেনু:</b>", reply_markup=channels_keyboard(), parse_mode="HTML")

    elif message.text == "📖 Help":
        help_txt = ("<b>📖 নির্দেশনা:</b>\n\n"
                    "<b>১. Setup Bot থেকে API এবং শর্টনার লিঙ্ক সেট করুন।</b>\n"
                    "<b>২. Manage Channels থেকে চ্যানেল যোগ করুন এবং বটকে এডমিন দিন।</b>\n"
                    "<b>৩. Create Post এ ক্লিক করে ছবি, নাম ও মেইন লিঙ্ক দিন।</b>\n"
                    "<b>৪. বট অটোমেটিক সব চ্যানেলে বোল্ড পোস্ট পাঠিয়ে দিবে।</b>")
        bot.send_message(user_id, help_txt, parse_mode="HTML")

# --- ৭. পোস্ট তৈরির স্টেপ-বাই-স্টেপ ---

def step_1_receive_logo(message):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "<b>❌ ভুল! ছবি পাঠান। আবার 'Create Post' এ ক্লিক করুন।</b>", parse_mode="HTML")
        return
    user_states[message.chat.id] = {'photo_id': message.photo[-1].file_id}
    msg = bot.send_message(message.chat.id, "<b>📝 এবার মুভি বা ড্রামার নাম লিখে পাঠান:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_2_receive_name)

def step_2_receive_name(message):
    user_states[message.chat.id]['movie_name'] = message.text.upper()
    msg = bot.send_message(message.chat.id, "<b>🔗 সবশেষে মুভির মেইন লিঙ্ক (Direct Link) পাঠান:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_3_final_process)

def step_3_final_process(message):
    user_id = message.chat.id
    main_url = message.text
    data = user_states.get(user_id)
    s = get_settings(user_id)

    if not data: return

    wait_msg = bot.send_message(user_id, "<b>⏳ লিঙ্ক শর্ট হচ্ছে এবং পোস্ট তৈরি হচ্ছে...</b>", parse_mode="HTML")
    short_link = get_short_link(main_url, s['api_key'], s['shortener_url'])

    # সম্পূর্ণ বোল্ড ডিজাইন (requested)
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

    # ইউজারকে প্রিভিউ
    bot.send_photo(user_id, data['photo_id'], caption=post_design, parse_mode='HTML')

    # চ্যানেলে অটো পোস্টিং
    success_count = 0
    for channel in s['channels']:
        try:
            bot.send_photo(channel, data['photo_id'], caption=post_design, parse_mode='HTML')
            success_count += 1
        except: pass

    bot.delete_message(user_id, wait_msg.message_id)
    bot.send_message(user_id, f"<b>✅ সফলভাবে পোস্ট তৈরি এবং {success_count}টি চ্যানেলে পাঠানো হয়েছে!</b>", reply_markup=main_keyboard(), parse_mode="HTML")
    user_states.pop(user_id, None)

# --- ৮. কলব্যাক ও ডেটাবেস ফাংশন ---

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.message.chat.id
    if call.data.startswith("set_"):
        field = call.data.replace("set_", "")
        msg = bot.send_message(user_id, "<b>📥 নতুন তথ্যটি লিখে পাঠান:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, update_db, field)
    
    elif call.data == "view_ch":
        s = get_settings(user_id)
        ch_text = "\n".join([f"<b>🔹 {c}</b>" for c in s['channels']]) if s['channels'] else "<b>❌ কোনো চ্যানেল নেই</b>"
        bot.send_message(user_id, f"<b>📢 আপনার চ্যানেলসমূহ:</b>\n\n{ch_text}", parse_mode="HTML")
    
    elif call.data == "add_ch":
        msg = bot.send_message(user_id, "<b>📥 চ্যানেলের ইউজারনেম দিন (@Username):</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, add_ch)
    
    elif call.data == "del_ch":
        msg = bot.send_message(user_id, "<b>🗑 ডিলিট করতে চ্যানেলের ইউজারনেম দিন:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, del_ch)
    
    bot.answer_callback_query(call.id)

def update_db(message, field):
    config_col.update_one({"user_id": message.chat.id}, {"$set": {field: message.text}})
    bot.send_message(message.chat.id, "<b>✅ তথ্য আপডেট হয়েছে!</b>", parse_mode="HTML", reply_markup=main_keyboard())

def add_ch(message):
    name = message.text.strip()
    if name.startswith("@"):
        config_col.update_one({"user_id": message.chat.id}, {"$addToSet": {"channels": name}})
        bot.send_message(message.chat.id, f"<b>✅ {name} যোগ করা হয়েছে!</b>", parse_mode="HTML", reply_markup=main_keyboard())
    else:
        bot.send_message(message.chat.id, "<b>❌ @ সহ ইউজারনেম দিন।</b>", parse_mode="HTML")

def del_ch(message):
    name = message.text.strip()
    config_col.update_one({"user_id": message.chat.id}, {"$pull": {"channels": name}})
    bot.send_message(message.chat.id, f"<b>🗑 {name} ডিলিট করা হয়েছে!</b>", parse_mode="HTML", reply_markup=main_keyboard())

# --- ৯. রান বট ---
if __name__ == '__main__':
    print("🤖 Bot is starting with 100% Support...")
    bot.infinity_polling()
