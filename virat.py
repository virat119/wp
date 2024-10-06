
import os
import time
import uuid
from flask import Flask, render_template, request, redirect, url_for, session as flask_session
from pyppeteer import launch
from colorama import Fore, Style, init
import qrcode
from flask import send_file
from werkzeug.utils import secure_filename

# Initialize colorama
init(autoreset=True)

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

active_sessions = {}

users = {
    "admin": "password123"  # Change this for real applications
}

def print_logo():
    return Fore.GREEN + Style.BRIGHT + """
    ██╗░░░██╗██╗██████╗░░█████╗░████████╗
    ██║░░░██║██║██╔══██╗██╔══██╗╚══██╔══╝
    ╚██╗░██╔╝██║██████╔╝███████║░░░██║░░░
    ░╚████╔╝░██║██╔══██╗██╔══██║░░░██║░░░
    ░░╚██╔╝░░██║██║░░██║██║░░██║░░░██║░░░
    ░░░╚═╝░░░╚═╝╚═╝░░╚═╝╚═╝░░╚═╝░░░╚═╝░░░
    WHATSAPP AUTOMATION TOOL
    """

@app.route('/')
def home():
    logo = print_logo()
    return render_template('index.html', logo=logo)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            flask_session['logged_in'] = True
            return redirect(url_for('home'))
        return "Invalid credentials, please try again."
    return render_template('login.html')

@app.route('/logout')
def logout():
    flask_session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if not flask_session.get('logged_in'):
        return redirect(url_for('login'))

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
        flask_session['session_name'] = session_name
        delay_seconds = int(request.form['delay_seconds'])
        target_number = request.form['target_number']

        task_id = str(uuid.uuid4())
        active_sessions[task_id] = True

        return redirect(url_for('task_page', task_id=task_id))

    return "Invalid file type. Only .txt files are allowed."

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/task/<task_id>')
def task_page(task_id):
    return render_template('task.html', task_id=task_id)

@app.route('/stop', methods=['POST'])
def stop_session():
    task_id = request.form['task_id']
    if task_id in active_sessions:
        active_sessions.pop(task_id)
        return f"Task with ID {task_id} has been stopped."
    return "Invalid task ID."

@app.route('/qrcode')
def qrcode_view():
    img = qrcode.make("https://web.whatsapp.com")
    img_path = os.path.join(app.static_folder, "qrcode.png")
    img.save(img_path)
    return send_file(img_path, mimetype='image/png')

@app.route('/generate_qrcode')
def generate_qrcode():
    img = qrcode.make("https://web.whatsapp.com")
    img_path = os.path.join(app.static_folder, "qrcode.png")
    img.save(img_path)
    return redirect(url_for('home'))

async def send_messages(task_id, file_path, delay_seconds, target_number):
    browser = await launch(headless=False)
    page = await browser.newPage()
    await page.goto('https://web.whatsapp.com')

    if task_id in active_sessions:
        print(Fore.CYAN + "QR code scan karein aur continue karne ke liye Enter dabayein...")
        input()

    try:
        with open(file_path, 'r') as file:
            messages = [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(Fore.RED + "\nFile padne mein error.")
        return

    colors = [Fore.GREEN, Fore.YELLOW, Fore.MAGENTA, Fore.BLUE, Fore.CYAN]
    color_index = 0

    async def send_message(index):
        nonlocal color_index
        if index >= len(messages):
            index = 0
        
        message = messages[index]
        await page.type('div[contenteditable="true"][data-tab="6"]', message + '\n')

        print(colors[color_index] + f"Message bheja: {message}")
        print(Fore.CYAN + "────────────────────────────────────────")
        color_index = (color_index + 1) % len(colors)

        await asyncio.sleep(delay_seconds)
        if task_id in active_sessions:
            await send_message(index + 1)

    await send_message(0)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
