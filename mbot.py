import telebot
from telebot import types
import json
import os

TOKEN = '7942083275:AAHWmCuIsQXCGgDIaJ0qNeU3NCiZO23jOGA'
bot = telebot.TeleBot(TOKEN)
DATA_FILE = 'users.json'

admin_id = 6606638731  # Replace with your real admin ID

tests = {
    'Matematika': [
        {'savol': '5 + 3 = ?', 'variantlar': ['7', '8', '9'], 'togri': '8'},
        {'savol': '6 * 7 = ?', 'variantlar': ['42', '36', '48'], 'togri': '42'}
    ],
    'Ingliz tili': [
        {'savol': '"Apple" so‘zining tarjimasi?', 'variantlar': ['Olma', 'Anor', 'Nok'], 'togri': 'Olma'},
    ]
}

mahsulotlar = [
    {'nomi': 'Qalam', 'narxi': 100},
    {'nomi': 'Daftar', 'narxi': 200}
]

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

users = load_data()

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('📚 Testlar', '🛍 Xarid qilish')
    markup.row('💰 Mening tangam', '👥 Referal havola')
    return markup

def test_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in tests.keys():
        markup.row(cat)
    markup.row('🔙 Orqaga')
    return markup

def product_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for item in mahsulotlar:
        markup.row(f"{item['nomi']} - {item['narxi']} coin")
    markup.row('🔙 Orqaga')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in users:
        ref = message.text.split(' ')
        referrer = ref[1] if len(ref) > 1 else None
        users[uid] = {'coins': 0, 'referrals': [], 'tests_done': [], 'referrer': referrer}
        if referrer and referrer in users:
            users[referrer]['coins'] += 100
            users[referrer]['referrals'].append(uid)
    save_data(users)
    bot.send_message(message.chat.id, "Xush kelibsiz!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid = str(message.from_user.id)
    txt = message.text

    if txt == '📚 Testlar':
        bot.send_message(message.chat.id, "Kategoriya tanlang:", reply_markup=test_menu())
    elif txt in tests:
        if txt in users[uid]['tests_done']:
            bot.send_message(message.chat.id, "Bu testni allaqachon ishlagansiz.")
        else:
            users[uid]['current_test'] = {'cat': txt, 'index': 0, 'correct': 0}
            save_data(users)
            send_question(message, uid)
    elif txt == '🛍 Xarid qilish':
        bot.send_message(message.chat.id, "Mahsulot tanlang:", reply_markup=product_menu())
    elif any(item['nomi'] in txt for item in mahsulotlar):
        buy_product(message, txt)
    elif txt == '💰 Mening tangam':
        bot.send_message(message.chat.id, f"Sizda {users[uid]['coins']} coin mavjud.")
    elif txt == '👥 Referal havola':
        link = f"https://t.me/raqibtestbot?start={uid}"
        bot.send_message(message.chat.id, f"Referal havolangiz: {link}")
    elif txt == '🔙 Orqaga':
        bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=main_menu())
    else:
        check_answer(message, uid, txt)

def send_question(message, uid):
    t = users[uid]['current_test']
    cat, idx = t['cat'], t['index']
    if idx >= len(tests[cat]):
        score = t['correct'] * 50
        users[uid]['coins'] += score
        users[uid]['tests_done'].append(cat)
        del users[uid]['current_test']
        save_data(users)
        bot.send_message(message.chat.id, f"Test yakunlandi! {score} coin olindi.", reply_markup=main_menu())
        return
    savol = tests[cat][idx]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for v in savol['variantlar']:
        markup.row(v)
    markup.row('🔙 Orqaga')
    bot.send_message(message.chat.id, savol['savol'], reply_markup=markup)

def check_answer(message, uid, javob):
    if 'current_test' not in users[uid]:
        return
    t = users[uid]['current_test']
    cat, idx = t['cat'], t['index']
    togri = tests[cat][idx]['togri']
    if javob == togri:
        users[uid]['current_test']['correct'] += 1
    users[uid]['current_test']['index'] += 1
    save_data(users)
    send_question(message, uid)

def buy_product(message, txt):
    uid = str(message.from_user.id)
    for item in mahsulotlar:
        if item['nomi'] in txt:
            if users[uid]['coins'] >= item['narxi']:
                users[uid]['coins'] -= item['narxi']
                save_data(users)
                bot.send_message(message.chat.id, f"Siz {item['nomi']} xarid qildingiz!")
                bot.send_message(admin_id, f"{message.from_user.first_name} ({uid}) {item['nomi']} xarid qildi.")
            else:
                bot.send_message(message.chat.id, "Tangalar yetarli emas!")
            break

@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.from_user.id != admin_id:
        return
    msg = message.text.replace('/broadcast', '').strip()
    for uid in users:
        try:
            bot.send_message(uid, f"📢 Admindan xabar: {msg}")
        except:
            continue

bot.polling()
