#libraries
import os
import sqlite3
import uuid
import secrets
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, session, url_for, redirect
# encryption for passwords
import bcrypt
from werkzeug.utils import secure_filename

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webshop.db')
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'images', 'avatars')

# only allow files of certain types 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


app.secret_key = 'secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

# Initialize database
def init_db():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL,
            avatar TEXT NOT NULL,
            email TEXT NOT NULL DEFAULT ''
        )
    ''')
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    #check if avatar and email columns exist
    if 'avatar' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar TEXT NOT NULL DEFAULT 'images/default_avatar.svg'")
    if 'email' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT NOT NULL DEFAULT ''")
    conn.commit()
    conn.commit()
    conn.close()

# connect the database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# check if the file meets the conditions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# save the avatar
def save_avatar(file, username):
    extension = file.filename.rsplit('.', 1)[1].lower()
    safe_name = secure_filename(f"{username}_{uuid.uuid4().hex}.{extension}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    file.save(file_path)
    return f"images/avatars/{safe_name}"

@app.context_processor
def inject_user():
    return {
        'logged_in': 'user_id' in session,
        'current_username': session.get('username'),
        'current_avatar': session.get('avatar'),
    }

# select the products from the database
def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT id, name, price, image_url FROM products').fetchall()
    conn.close()
    return products

# search bar code 
def search_products(query):
    query = (query or '').strip()
    if not query:
        return []

    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM products').fetchall()
    conn.close()

    query_lower = query.lower()
    terms = [term for term in query_lower.split() if term]
    results = []

    for row in rows:
        name = (row['name'] or '').lower()
        description = (row['description'] or '').lower()
        score = 0

        if query_lower in name:
            score += 10
        if query_lower in description:
            score += 7

        for term in terms:
            if term in name:
                score += 2
            if term in description:
                score += 1

        if score > 0:
            results.append((score, row))

    results.sort(key=lambda item: (-item[0], item[1]['name']))
    return [product for score, product in results]


# get favorite products from session
def get_favorite_products():
    fav_ids = session.get('favorites', [])
    if not fav_ids:
        return []
    conn = get_db_connection()
    placeholders = ','.join('?' for _ in fav_ids)
    query = f'SELECT * FROM products WHERE id IN ({placeholders})'
    rows = conn.execute(query, tuple(fav_ids)).fetchall()
    conn.close()
    # preserve order of fav_ids
    rows_by_id = {row['id']: row for row in rows}
    return [rows_by_id[i] for i in fav_ids if i in rows_by_id]

# main page
@app.route('/')
def index():
    products = get_products()
    return render_template('main.html', products=products)

# logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# login page 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error='Username and password required')
        
        conn = get_db_connection()
        # allow login by username/email
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, username)).fetchone()
        conn.close()
        
        # encrypt the password for good cybersecurity
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['avatar'] = user['avatar'] if 'avatar' in user.keys() else 'images/default_avatar.svg'
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

# signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        avatar_file = request.files.get('avatar')

        if not username or not password or not email:
            return render_template('signup.html', error='Username and password required')
        
        if password != password_confirm:
            return render_template('signup.html', error='Passwords do not match')

        avatar_path = 'images/default_avatar.svg'
        if avatar_file and avatar_file.filename:
            if not allowed_file(avatar_file.filename):
                return render_template('signup.html', error='Allowed image types: png, jpg, jpeg, gif')
            avatar_path = save_avatar(avatar_file, username)

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            conn = get_db_connection()
            # check for existing username / email
            existing = conn.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
            if existing:
                conn.close()
                return render_template('signup.html', error='Username or email already exists')
            conn.execute('INSERT INTO users (username, password, avatar, email) VALUES (?, ?, ?, ?)', (username, hashed, avatar_path, email))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            return render_template('signup.html', error='Username or email already exists')

        return redirect(url_for('login'))

    return render_template('signup.html')

# email code DOESN'T WORK ON PYTHONANYWHERE
def send_email(to_address, subject, body):
    smtp_host = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = 'webshopmail.ic@gmail.com'
    smtp_pass = 'tfuz wzis twxc dwpr'
    from_addr = 'webshopmail.ic@gmail.com'

    if not smtp_host or not from_addr:
        raise RuntimeError('Email server not configured. Set EMAIL_HOST and EMAIL_FROM (and optionally EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD)')

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_address
    msg.set_content(body)

    # ports
    if smtp_port == 465:
        server = smtplib.SMTP_SSL(smtp_host, smtp_port)
    else:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()

    try:
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
        server.send_message(msg)
    finally:
        try:
            server.quit()
        except Exception:
            pass

# forgot password page
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        if not identifier:
            return render_template('forgot_password.html', error='Enter username or email')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (identifier, identifier)).fetchone()
        if not user:
            conn.close()
            # don't reveal user existence
            return render_template('forgot_password.html', success='If an account exists, an email has been sent')

        # generate new password
        new_password = secrets.token_urlsafe(8)
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed, user['id']))
        conn.commit()
        conn.close()

        # attempt to send email
        try:
            send_email(user['email'], 'Password reset', f'Your new password: {new_password}\nPlease log in and change it.')
        except Exception as e:
            return render_template('forgot_password.html', error=f'Failed to send email: {e}')

        return render_template('forgot_password.html', success='If an account exists, an email has been sent')

    return render_template('forgot_password.html')

# delete the account if wanted
@app.route('/delete-account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (session['user_id'],))
    conn.commit()
    conn.close()
    session.clear()
    return redirect(url_for('index'))

# change password page
@app.route('/profile/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'GET':
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        return render_template('change_password.html', user=user)

    # POST handling
    current = request.form.get('current_password')
    new = request.form.get('new_password')
    confirm = request.form.get('new_password_confirm')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    if not current or not new or not confirm:
        conn.close()
        return render_template('change_password.html', user=user, error='All password fields are required')

    if new != confirm:
        conn.close()
        return render_template('change_password.html', user=user, error='New passwords do not match')

    if not user or not bcrypt.checkpw(current.encode('utf-8'), user['password']):
        conn.close()
        return render_template('change_password.html', user=user, error='Current password is incorrect')

    hashed = bcrypt.hashpw(new.encode('utf-8'), bcrypt.gensalt())
    conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed, user['id']))
    conn.commit()
    # reload user to show any updates
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('change_password.html', user=user, success='Password changed successfully')

# profile page
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if user is None:
        conn.close()
        session.clear()
        return redirect(url_for('login'))

    error = None
    success = None

    if request.method == 'POST':
        avatar_file = request.files.get('avatar')
        if not avatar_file or not avatar_file.filename:
            error = 'Please choose an image to upload.'
        elif not allowed_file(avatar_file.filename):
            error = 'Allowed image types: png, jpg, jpeg, gif'
        else:
            avatar_path = save_avatar(avatar_file, user['username'])
            conn.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar_path, user['id']))
            conn.commit()
            session['avatar'] = avatar_path
            success = 'Profile picture updated successfully.'
            user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    conn.close()
    return render_template('profile.html', user=user, error=error, success=success)

# shoplist page
@app.route('/shoplist', methods=['GET', 'POST'])
def shoplist():
    # shoplist template removed — redirect to home listing
    return redirect(url_for('index'))

# search page
@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('q', '').strip()
    products = search_products(query)
    return render_template('search.html', query=query, products=products)

# product page
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    # get the product from the database
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product is None:
        return "Product not found", 404
    return render_template('product.html', product=product)


# Toggle favorite for a product
@app.route('/favorites/toggle/<int:product_id>', methods=['POST'])
def toggle_favorite(product_id):
    favs = session.get('favorites', [])
    # ensure ints
    favs = [int(i) for i in favs]
    if product_id in favs:
        favs.remove(product_id)
    else:
        favs.append(product_id)
    session['favorites'] = favs
    session.modified = True
    # redirect back to where the request came from
    return redirect(request.referrer or url_for('index'))


# Favorites list page
@app.route('/favorites')
def favorites():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    products = get_favorite_products()
    return render_template('favorites.html', products=products)


# Cart page
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # show favorite products as selectable items
    products = get_favorite_products()
    return render_template('cart.html', products=products)

# checkout page -> won't finish
@app.route('/cart/checkout', methods=['POST'])
def cart_checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # selected product ids come from form 'selected'
    selected = request.form.getlist('selected')
    # convert to ints
    try:
        selected_ids = [int(i) for i in selected]
    except ValueError:
        selected_ids = []

    # fetch product rows for selected ids
    conn = get_db_connection()
    products = []
    if selected_ids:
        placeholders = ','.join('?' for _ in selected_ids)
        rows = conn.execute(f'SELECT * FROM products WHERE id IN ({placeholders})', tuple(selected_ids)).fetchall()
        # preserve order of selected_ids
        rows_by_id = {row['id']: row for row in rows}
        products = [rows_by_id[i] for i in selected_ids if i in rows_by_id]
    conn.close()

    # store in session for later (optional)
    session['cart'] = selected_ids
    session.modified = True

    # render a confirmation page with a Pay button (not implemented)
    return render_template('cart_confirm.html', products=products)

if __name__ == '__main__':
    init_db()  # Initialize database
    app.run(debug=True)