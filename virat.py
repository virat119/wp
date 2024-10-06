

import os
import time
import asyncio
import base64
from flask import Flask, render_template, request, redirect, url_for, session as flask_session
from pyppeteer import launch  # Browser automation ke liye Pyppeteer
from colorama import Fore, Style, init
import qrcode  # QR code generate karne ke liye
from flask import send_file
from werkzeug.utils import secure_filename

# Colorama initialize karna
init(autoreset=True)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Flask session ke liye secret key
app.config['UPLOAD_FOLDER'] = 'uploads'  # Uploaded files ke liye folder
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

# Ensure karna ki upload folder exist kare
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Naya Logo
def print_logo():
    return Fore.GREEN + Style.BRIGHT + """
    ██╗░░░██╗██╗██████╗░░█████╗░████████╗
    ██║░░░██║██║██╔══██╗██╔══██╗╚══██╔══╝
    ╚██╗░██╔╝██║██████╔╝███████║░░░██║░░░
    ░╚████╔╝░██║██╔══██╗██╔══██║░░░██║░░░
    ░░╚██╔╝░░██║██║░░██║██║░░██║░░░██║░░░
    ░░░╚═╝░░░╚═╝╚═╝░░╚═╝╚═╝░░╚═╝░░░╚═╝░░░
    WHATSAPP AUTOMATION TOOL
    CREATED BY VIRAT ROY
    CONTACT: +91 6352569270
    """

@app.route('/')
def home():
    logo = print_logo()
    return render_template('index.html', logo=logo)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        session_name = request.form['session_name']
        flask_session['session_name'] = session_name  # Save session name in Flask session
        delay_seconds = int(request.form['delay_seconds'])
        target_number = request.form['target_number']
        
        # Check if session already exists
        if 'logged_in' in flask_session and flask_session['session_name'] == session_name:
            print(Fore.GREEN + "User already logged in with session:", session_name)
        else:
            print(Fore.YELLOW + "New session started:", session_name)
            flask_session['logged_in'] = True  # Set logged in status

        asyncio.run(send_messages(session_name, file_path, delay_seconds, target_number))
        return redirect(url_for('home'))

    return "Invalid file type. Only .txt files are allowed."

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/start', methods=['POST'])
def start():
    session_name = request.form['session_name']
    file_path = request.form['file_path']
    delay_seconds = int(request.form['delay_seconds'])
    target_number = request.form['target_number']

    if 'logged_in' in flask_session and flask_session['session_name'] == session_name:
        asyncio.run(send_messages(session_name, file_path, delay_seconds, target_number))
    else:
        print(Fore.RED + "Session not found. Please upload a file to start.")
    
    return redirect(url_for('home'))

@app.route('/qrcode')
def qrcode_view():
    # QR code generate karna
    img = qrcode.make("https://web.whatsapp.com")
    img.save("static/qrcode.png")
    return send_file("static/qrcode.png", mimetype='image/png')

async def send_messages(session_name, file_path, delay_seconds, target_number):
    browser = await launch(headless=False)
    page = await browser.newPage()
    await page.goto('https://web.whatsapp.com')

    if 'logged_in' in flask_session and flask_session['session_name'] == session_name:
        print(Fore.CYAN + "QR code scan karein aur continue karne ke liye Enter dabayein...")
        input()

    # File se messages read karna
    try:
        with open(file_path, 'r') as file:
            messages = [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(Fore.RED + "\nFile padne mein error. Kripya file path check karein.")
        return

    colors = [Fore.GREEN, Fore.YELLOW, Fore.MAGENTA, Fore.BLUE, Fore.CYAN]
    color_index = 0

    async def send_message(index):
        nonlocal color_index
        if index >= len(messages):
            index = 0
        
        message = messages[index]
        await page.type('div[contenteditable="true"][data-tab="6"]', message + '\n')  # Message bhejna

        # Message status print karna
        timestamp = time.strftime('%d/%m/%Y %H:%M:%S')
        print(colors[color_index] + f"Message bheja: {message}")
        print(colors[color_index] + f"To: {target_number}")
        print(colors[color_index] + f"At: {timestamp}")
        print(colors[color_index] + f"Delay ke baad: {delay_seconds} seconds")
        print(Fore.CYAN + "────────────────────────────────────────")  # Line separator
        color_index = (color_index + 1) % len(colors)

        await asyncio.sleep(delay_seconds)
        await send_message(index + 1)

    await send_message(0)

    await browser.close()

@app.route('/logout')
def logout():
    flask_session.pop('logged_in', None)
    flask_session.pop('session_name', None)
    print(Fore.GREEN + "User logged out successfully.")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
