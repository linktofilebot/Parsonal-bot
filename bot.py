import os
import subprocess
import sys

# --- ১. অটো লাইব্রেরি ইন্সটলেশন (Auto Install Requirements) ---
def install_requirements():
    requirements = ['pyTelegramBotAPI', 'pymongo', 'requests', 'dnspython']
    for lib in requirements:
        try:
            __import__(lib if lib != 'pyTelegramBotAPI' else 'telebot')
        except ImportError:
            print(f"Installing {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

# কোড রান হওয়ার সাথে সাথে লাইব্রেরি চেক করবে
install_requirements()

import telebot
import requests
import pymongo
from telebot import types

# --- ২. কনফিগারেশন (Configuration) ---
BOT_TOKEN = '8348660690:AAEAQUDHJm5QTZv4YMr7DrvddYPvzQF0-Wk' 
MONGO_URL = 'mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

# --- ৩. ডাটাবেস কানেকশন (Database Connection) ---
try:
    client = pymongo.MongoClient(MONGO_URL)
    db = client['ProMovieBot_Final']
    config_col = db['user_configs']
    print("✅ MongoDB Connected Successfully!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    sys.exit()

bot = telebot.TeleBot(BOT_TOKEN)

# ইউজার স্টেট ট্র্যাক করার জন্য মেমোরি (Temporary Storage)
user_states = {}

# ডাটাবেস থেকে সেটিংস লোড করার ফাংশন
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

# --- ৪. কিবোর্ড মেনু (Keyboards) ---

def main_keyboard():
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
        types.InlineKeyboardButton("🔗 Shortener URL", callback_data="set_url"),
        types.InlineKeyboardButton("📥 Guide Link", callback_data="set_guide"),
        types.InlineKeyboardButton("📢 Channels", callback_data="set_channels"),
        types.InlineKeyboardButton("🔞 Backup Link", callback_data="set_backup"),
        types.InlineKeyboardButton("🔗 Share Link", callback_data="set_share")
    )
    return markup

# --- ৫. লিঙ্ক শর্টনার লজিক (URL Shortener Logic) ---
def get_short_link(long_url, api_key, api_url):
    if api_key == "None" or not api_key:
        return long_url
    try:
        clean_url = api_url.split('?')[0].strip()
        params = {'api': api_key, 'url': long_url}
        res = requests.get(clean_url, params=params, timeout=15)
        
        if res.status_code == 200:
            try:
                data = res.json()
                # শর্টনার অনুযায়ী বিভিন্ন ফরম্যাট হ্যান্ডলিং
                return data.get('shortenedUrl', data.get('url', res.text.strip()))
            except:
                return res.text.strip()
        return long_url
    except:
        return long_url

# --- ৬. মেইন মেসেজ হ্যান্ডলারস (Message Handlers) ---

@bot.message_handler(commands=['start'])
def start_bot(message):
    get_settings(message.chat.id)
    bot.send_message(
        message.chat.id, 
        "🚀 <b>মুভি পোস্ট মেকার প্রলু ভার্সনে স্বাগতম!</b>\n\nসবকিছু কন্ট্রোল করার জন্য নিচের বাটনগুলো ব্যবহার করুন।",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda message: True)
def handle_reply_buttons(message):
    user_id = message.chat.id
    if message.text == "🆕 Create Post":
        msg = bot.send_message(user_id, "🖼 <b>প্রথমে মুভির লগো বা পোস্টার (ছবি) পাঠান:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, step_1_receive_logo)

    elif message.text == "📋 My Settings":
        s = get_settings(user_id)
        ch_list = ", ".join(s['channels']) if s['channels'] else "None"
        info = (f"📊 <b>আপনার বর্তমান সেটিংস:</b>\n\n"
                f"🔊 ভাষা: <code>{s['lang']}</code>\n"
                f"💿 এপিসোড: <code>{s['eps']}</code>\n"
                f"🔗 API URL: <code>{s['shortener_url']}</code>\n"
                f"🔑 API Key: <code>{s['api_key']}</code>\n"
                f"📢 চ্যানেল: <code>{ch_list}</code>")
        bot.send_message(user_id, info, reply_markup=main_keyboard(), parse_mode="HTML")

    elif message.text == "⚙️ Setup Bot":
        bot.send_message(user_id, "⚙️ <b>কোন তথ্যটি পরিবর্তন করতে চান?</b>", reply_markup=setup_inline(), parse_mode="HTML")

    elif message.text == "📖 Help":
        help_txt = ("📖 <b>নির্দেশনা:</b>\n\n"
                    "১. প্রথমে 'Setup Bot' এ গিয়ে API Key ও চ্যানেল সেট করুন।\n"
                    "২. বটকে অবশ্যই আপনার চ্যানেলে Admin বানাতে হবে।\n"
                    "৩. 'Create Post' এ ক্লিক করে ছবি, নাম ও লিঙ্ক দিন।\n"
                    "৪. বট অটোমেটিক লিঙ্ক শর্ট করে আপনার চ্যানেলে পাঠিয়ে দিবে।")
        bot.send_message(user_id, help_txt, parse_mode="HTML")

# --- ৭. পোস্ট তৈরির স্টেপ-বাই-স্টেপ সিস্টেম ---

def step_1_receive_logo(message):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "❌ এটি ছবি নয়! আবার 'Create Post' ক্লিক করুন।")
        return
    user_states[message.chat.id] = {'photo_id': message.photo[-1].file_id}
    msg = bot.send_message(message.chat.id, "📝 <b>এবার মুভি বা ড্রামার নাম লিখে পাঠান:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_2_receive_name)

def step_2_receive_name(message):
    user_states[message.chat.id]['movie_name'] = message.text.upper()
    msg = bot.send_message(message.chat.id, "🔗 <b>সবশেষে মুভির মেইন লিঙ্ক (Direct URL) পাঠান:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, step_3_final_process)

def step_3_final_process(message):
    user_id = message.chat.id
    main_url = message.text
    data = user_states.get(user_id)
    s = get_settings(user_id)

    if not data:
        bot.send_message(user_id, "❌ এরর হয়েছে, নতুন করে শুরু করুন।")
        return

    wait_msg = bot.send_message(user_id, "⏳ <b>প্রসেসিং... লিঙ্ক শর্ট করা হচ্ছে।</b>", parse_mode="HTML")

    # লিঙ্ক শর্ট করা
    short_link = get_short_link(main_url, s['api_key'], s['shortener_url'])

    # ডিজাইন (Bold Labels + Code Content)
    post_design = f"""
╔════════════════════════╗
     ✨ <b>{data['movie_name']}</b> ✨
╚════════════════════════╝

🎬 <b>Drama Name :</b> <code>{data['movie_name']}</code>
🔊 <b>Language   :</b> <code>{s['lang']}</code>
💿 <b>Episodes   :</b> <code>{s['eps']}</code>

📥 <b>Watch / Download Link:</b>
🔗 <code>{short_link}</code>

📥 <b>How to Download:</b>
🔗 <code>{s['dl_guide']}</code>

📢 <b>Share Channel:</b>
🔗 <code>{s['share_link']}</code>

🔞 <b>Join Our Backup Channel:</b>
🔗 <code>{s['backup_link']}</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━
   🍿 <b>ENJOY YOUR DRAMA</b> 🍿
    """

    # ইউজারকে প্রিভিউ পাঠানো (ক্লিক টু কপি)
    bot.send_photo(user_id, data['photo_id'], caption=post_design, parse_mode='HTML')

    # সেট করা চ্যানেলগুলোতে অটো পোস্টিং
    success_count = 0
    for channel in s['channels']:
        try:
            bot.send_photo(channel, data['photo_id'], caption=post_design, parse_mode='HTML')
            success_count += 1
        except Exception as e:
            print(f"Error posting to {channel}: {e}")

    bot.delete_message(user_id, wait_msg.message_id)
    bot.send_message(user_id, f"✅ <b>পোস্ট তৈরি এবং {success_count}টি চ্যানেলে পাঠানো হয়েছে!</b>", reply_markup=main_keyboard(), parse_mode="HTML")
    
    # মেমোরি ক্লিয়ার
    user_states.pop(user_id, None)

# --- ৮. সেটিংস আপডেট সিস্টেম (Inline Callback) ---

@bot.callback_query_handler(func=lambda call: True)
def handle_setup_callbacks(call):
    labels = {
        "set_lang": "Language", "set_eps": "Episodes", "set_api": "Shortener API Key",
        "set_url": "Shortener API URL", "set_guide": "Guide Link",
        "set_channels": "Channels (@ch1, @ch2)", "set_backup": "Backup Link", "set_share": "Share Link"
    }
    field = call.data.replace("set_", "")
    if call.data in labels:
        msg = bot.send_message(call.message.chat.id, f"📥 নতুন <b>{labels[call.data]}</b> লিখে পাঠান:", parse_mode="HTML")
        bot.register_next_step_handler(msg, update_config_in_db, field)
    bot.answer_callback_query(call.id)

def update_config_in_db(message, field):
    user_id = message.chat.id
    val = message.text
    if field == "channels":
        val = [c.strip() for c in val.split(',')]
    
    config_col.update_one({"user_id": user_id}, {"$set": {field: val}})
    bot.send_message(user_id, "✅ <b>তথ্যটি সফলভাবে আপডেট করা হয়েছে!</b>", reply_markup=main_keyboard(), parse_mode="HTML")

# --- ৯. বট রান করা ---
if __name__ == '__main__':
    print("🤖 Bot is starting up...")
    bot.infinity_polling()
