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
# --- কনফিগারেশন (এখানে আপনার তথ্য দিন) ---
# ==========================================
BOT_TOKEN = '8348660690:AAEAQUDHJm5QTZv4YMr7DrvddYPvzQF0-Wk'  # @BotFather থেকে নিন
MONGO_URL = 'mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0' # MongoDB Atlas থেকে নিন
# ==========================================

# ডাটাবেস কানেকশন
try:
    client = pymongo.MongoClient(MONGO_URL)
    db = client['FinalMovieBot']
    config_col = db['user_configs']
    print("✅ MongoDB Connected Successfully!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    sys.exit()

bot = telebot.TeleBot(BOT_TOKEN)

# ডিফল্ট সেটিংস ফাংশন
def get_user_data(user_id):
    data = config_col.find_one({"user_id": user_id})
    if not data:
        default_data = {
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
        config_col.insert_one(default_data)
        return default_data
    return data

# --- কিবোর্ড মেনু ---
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

# --- শর্টনার লজিক ---
def shorten_link(long_url, api_key, api_url):
    if api_key == "None" or not api_key:
        return long_url
    try:
        params = {'api': api_key, 'url': long_url, 'format': 'text'}
        res = requests.get(api_url, params=params, timeout=10)
        return res.text.strip() if res.status_code == 200 else long_url
    except:
        return long_url

# --- হ্যান্ডলারস ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    get_user_data(message.chat.id)
    bot.send_message(
        message.chat.id, 
        "🚀 **মুভি পোস্ট মেকার প্রলু ভার্সনে স্বাগতম!**\n\nনিচের বাটনগুলো ব্যবহার করে আপনার সেটিংস সেটআপ করুন এবং দ্রুত পোস্ট তৈরি করুন।",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.chat.id
    text = message.text

    if text == "🆕 Create Post":
        msg = bot.send_message(user_id, "🎬 **মুভির নাম এবং লিঙ্কটি পাঠান।**\n\nফরম্যাট: `নাম | লিঙ্ক`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, start_post_making)

    elif text == "📋 My Settings":
        s = get_user_data(user_id)
        channels = ", ".join(s['channels']) if s['channels'] else "None"
        info = (f"📊 **আপনার বর্তমান কনফিগারেশন:**\n\n"
                f"🔊 ভাষা: {s['lang']}\n"
                f"💿 এপিসোড: {s['eps']}\n"
                f"🔗 API URL: {s['shortener_url']}\n"
                f"🔑 API Key: {s['api_key']}\n"
                f"📥 গাইড লিঙ্ক: {s['dl_guide']}\n"
                f"📢 চ্যানেলসমূহ: {channels}")
        bot.send_message(user_id, info, reply_markup=main_keyboard())

    elif text == "⚙️ Setup Bot":
        bot.send_message(user_id, "⚙️ **সেটিংস পরিবর্তন করতে নিচের বাটনে ক্লিক করুন:**", reply_markup=setup_inline())

    elif text == "📖 Help":
        help_text = (
            "📖 **কিভাবে ব্যবহার করবেন?**\n\n"
            "১. প্রথমে 'Setup Bot' থেকে API Key ও চ্যানেল সেট করুন।\n"
            "২. বটকে অবশ্যই চ্যানেলে Admin বানাতে হবে।\n"
            "৩. 'Create Post' এ ক্লিক করে 'Movie Name | Link' পাঠান।\n"
            "৪. বট অটোমেটিক লিঙ্ক সর্ট করে আপনার চ্যানেলে ডিজাইনসহ পাঠিয়ে দিবে।"
        )
        bot.send_message(user_id, help_text)

# --- সেটিংস আপডেট লজিক ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    labels = {
        "set_lang": "Language", "set_eps": "Episodes", "set_api": "API Key",
        "set_url": "Shortener API URL", "set_guide": "Guide Link",
        "set_channels": "Channels (যেমন: @ch1, @ch2)", "set_backup": "Backup Link",
        "set_share": "Share Link"
    }
    field = call.data.replace("set_", "")
    if call.data in labels:
        msg = bot.send_message(call.message.chat.id, f"📥 নতুন **{labels[call.data]}** লিখে পাঠান:")
        bot.register_next_step_handler(msg, update_db, field)
    bot.answer_callback_query(call.id)

def update_db(message, field):
    user_id = message.chat.id
    val = message.text
    if field == "channels":
        val = [c.strip() for c in val.split(',')]
    
    config_col.update_one({"user_id": user_id}, {"$set": {field: val}})
    bot.send_message(user_id, "✅ তথ্যটি সফলভাবে আপডেট করা হয়েছে!", reply_markup=main_keyboard())

# --- পোস্ট তৈরি ও অটো পোস্টিং ---
def start_post_making(message):
    user_id = message.chat.id
    if "|" not in message.text:
        bot.send_message(user_id, "❌ ভুল ফরম্যাট! (নাম | লিঙ্ক) এভাবে দিন।", reply_markup=main_keyboard())
        return

    try:
        name_input, link_input = message.text.split("|")
        m_name = name_input.strip().upper()
        m_link = link_input.strip()

        s = get_user_data(user_id)
        wait = bot.send_message(user_id, "⏳ প্রসেসিং শুরু হয়েছে...")

        # লিঙ্ক শর্ট করা
        short_url = shorten_link(m_link, s['api_key'], s['shortener_url'])

        # ডিজাইন
        final_post = f"""
╔════════════════════════╗
     ✨ {m_name} ✨
╚════════════════════════╝

🎬 Drama Name : {m_name}
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

        # ইউজারকে কপি করার জন্য পাঠানো
        bot.send_message(user_id, f"<code>{final_post}</code>", parse_mode='HTML')

        # চ্যানেলসমূহে পাঠানো
        success = 0
        for ch in s['channels']:
            try:
                bot.send_message(ch, final_post, parse_mode='HTML')
                success += 1
            except:
                pass

        bot.delete_message(user_id, wait.message_id)
        bot.send_message(user_id, f"✅ কাজ শেষ!\n🚀 চ্যানেলে পোস্ট হয়েছে: {success}টি", reply_markup=main_keyboard())

    except Exception as e:
        bot.send_message(user_id, f"❌ ত্রুটি: {str(e)}")

# বট রান
if __name__ == '__main__':
    print("🤖 Bot is Online...")
    bot.infinity_polling()
