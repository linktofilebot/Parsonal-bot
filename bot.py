import os
import subprocess
import sys

# --- অটো লাইব্রেরি ইনস্টলেশন সিস্টেম ---
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

# ==========================================
# --- আপনার দেওয়া কনফিগারেশন ---
# ==========================================
BOT_TOKEN = '8348660690:AAEAQUDHJm5QTZv4YMr7DrvddYPvzQF0-Wk' 
MONGO_URL = 'mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
# ==========================================

# ডাটাবেস সেটআপ
try:
    client = pymongo.MongoClient(MONGO_URL)
    db = client['FinalMovieBot_V3']
    config_col = db['user_configs']
    print("✅ MongoDB Connected Successfully!")
except Exception as e:
    print(f"❌ MongoDB Error: {e}")
    sys.exit()

bot = telebot.TeleBot(BOT_TOKEN)

# ইউজার স্টেট ট্র্যাক করার জন্য
user_states = {}

# ডাটাবেস থেকে সেটিংস নেওয়া
def get_settings(user_id):
    data = config_col.find_one({"user_id": user_id})
    if not data:
        default = {
            "user_id": user_id,
            "lang": "Hindi Dubbed",
            "eps": "All Episodes Added",
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

# --- কিবোর্ড মেনু ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🆕 Create Post", "📋 My Settings")
    markup.row("⚙️ Setup Bot", "📖 Help")
    return markup

def setup_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔊 Language", callback_data="set_lang"),
        types.InlineKeyboardButton("💿 Episodes", callback_data="set_eps"),
        types.InlineKeyboardButton("🔑 API Key", callback_data="set_api"),
        types.InlineKeyboardButton("🔗 Shortener URL", callback_data="set_shortener_url"),
        types.InlineKeyboardButton("📥 Guide Link", callback_data="set_dl_guide"),
        types.InlineKeyboardButton("📢 Channels", callback_data="set_channels"),
        types.InlineKeyboardButton("🔞 Backup Link", callback_data="set_backup"),
        types.InlineKeyboardButton("🔗 Share Link", callback_data="set_share")
    )
    return markup

# --- লিঙ্ক শর্টনার লজিক ---
def get_short_link(long_url, api_key, api_url):
    if api_key == "None" or not api_key:
        return long_url
    try:
        # API URL ক্লিন করা
        clean_url = api_url.split('?')[0]
        params = {'api': api_key, 'url': long_url}
        res = requests.get(clean_url, params=params, timeout=15)
        
        if res.status_code == 200:
            try:
                data = res.json()
                return data.get('shortenedUrl', data.get('url', long_url))
            except:
                return res.text.strip()
        return long_url
    except:
        return long_url

# --- মেইন হ্যান্ডলারস ---
@bot.message_handler(commands=['start'])
def welcome(message):
    get_settings(message.chat.id)
    bot.send_message(
        message.chat.id, 
        "🚀 **মুভি পোস্ট মেকার প্রলু ভার্সনে স্বাগতম!**\n\nসবকিছু কন্ট্রোল করার জন্য নিচের বাটনগুলো ব্যবহার করুন।",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.chat.id
    if message.text == "🆕 Create Post":
        msg = bot.send_message(user_id, "🖼 **প্রথমে মুভির লগো বা পোস্টার (ছবি) পাঠান:**")
        bot.register_next_step_handler(msg, process_logo_step)

    elif message.text == "📋 My Settings":
        s = get_settings(user_id)
        ch_list = ", ".join(s['channels']) if s['channels'] else "None"
        info = (f"📊 **আপনার বর্তমান সেটিংস:**\n\n"
                f"🔊 ভাষা: {s['lang']}\n"
                f"💿 এপিসোড: {s['eps']}\n"
                f"🔗 API URL: {s['shortener_url']}\n"
                f"🔑 API Key: {s['api_key']}\n"
                f"📢 চ্যানেল: {ch_list}")
        bot.send_message(user_id, info, reply_markup=main_menu())

    elif message.text == "⚙️ Setup Bot":
        bot.send_message(user_id, "⚙️ **সেটিংস পরিবর্তন করতে নিচের বাটন ক্লিক করুন:**", reply_markup=setup_inline())

    elif message.text == "📖 Help":
        bot.send_message(user_id, "নির্দেশনা:\n১. Setup বাটন থেকে API Key ও Shortener URL সেট করুন।\n২. চ্যানেল ইউজারনেম (@ChannelName) সেট করুন।\n৩. Create Post এ ক্লিক করে স্টেপগুলো ফলো করুন।")

# --- পোস্ট তৈরির স্টেপ বাই স্টেপ লজিক ---

def process_logo_step(message):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "❌ এটি ছবি নয়! আবার 'Create Post' এ ক্লিক করুন।")
        return
    user_states[message.chat.id] = {'photo': message.photo[-1].file_id}
    msg = bot.send_message(message.chat.id, "📝 **এবার মুভি বা ড্রামার নাম লিখে পাঠান:**")
    bot.register_next_step_handler(msg, process_name_step)

def process_name_step(message):
    user_states[message.chat.id]['name'] = message.text.upper()
    msg = bot.send_message(message.chat.id, "🔗 **সবশেষে মুভির মেইন লিঙ্কটি (Link) পাঠান:**")
    bot.register_next_step_handler(msg, process_final_step)

def process_final_step(message):
    user_id = message.chat.id
    main_url = message.text
    data = user_states.get(user_id)
    s = get_settings(user_id)

    if not data:
        bot.send_message(user_id, "❌ কিছু ভুল হয়েছে, আবার শুরু করুন।")
        return

    wait = bot.send_message(user_id, "⏳ লিঙ্ক শর্ট হচ্ছে এবং পোস্ট তৈরি হচ্ছে...")
    
    # লিঙ্ক শর্ট করা
    short_url = get_short_link(main_url, s['api_key'], s['shortener_url'])

    # ডিজাইন ফরম্যাট
    post_design = f"""
╔════════════════════════╗
     ✨ {data['name']} ✨
╚════════════════════════╝

🎬 Drama Name : {data['name']}
🔊 Language   : {s['lang']}
💿 Episodes   : {s['eps']}

📥 Watch / Download Link:
🔗 {short_url}

📥 How to Download:
🔗 {s['dl_guide']}

📢 Share Channel:
🔗 {s['share_link']}

🔞 Join Our Backup Channel:
🔗 {s['backup_link']}

━━━━━━━━━━━━━━━━━━━━━━━━━━
     🍿 ENJOY YOUR DRAMA 🍿
    """

    # ইউজারকে প্রিভিউ (ক্লিক টু কপি মোড)
    bot.send_photo(user_id, data['photo'], caption=f"<code>{post_design}</code>", parse_mode='HTML')

    # চ্যানেলে অটো পোস্ট
    success = 0
    for ch in s['channels']:
        try:
            bot.send_photo(ch, data['photo'], caption=post_design, parse_mode='HTML')
            success += 1
        except: pass

    bot.delete_message(user_id, wait.message_id)
    bot.send_message(user_id, f"✅ পোস্ট তৈরি এবং {success}টি চ্যানেলে পাঠানো হয়েছে!", reply_markup=main_menu())
    user_states.pop(user_id, None) # ডাটা ক্লিয়ার

# --- সেটিংস আপডেট বাটন হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    labels = {
        "set_lang": "Language", "set_eps": "Episodes", "set_api": "API Key",
        "set_shortener_url": "Shortener API URL", "set_dl_guide": "Guide Link",
        "set_channels": "Channels (@ch1, @ch2)", "set_backup": "Backup Link",
        "set_share": "Share Link"
    }
    field = call.data.replace("set_", "")
    if call.data in labels:
        msg = bot.send_message(call.message.chat.id, f"📥 আপনার নতুন **{labels[call.data]}** লিখে পাঠান:")
        bot.register_next_step_handler(msg, update_settings_db, field)
    bot.answer_callback_query(call.id)

def update_settings_db(message, field):
    user_id = message.chat.id
    val = message.text
    if field == "channels":
        val = [c.strip() for c in val.split(',')]
    
    config_col.update_one({"user_id": user_id}, {"$set": {field: val}})
    bot.send_message(user_id, "✅ তথ্যটি সফলভাবে আপডেট করা হয়েছে!", reply_markup=main_menu())

# বট চালু
if __name__ == '__main__':
    print("🤖 Bot is Online...")
    bot.infinity_polling()
