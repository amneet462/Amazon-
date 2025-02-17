#######################################################################
#                                                                     #
#   * I used Claude 3.5 Sonnet to help fix bugs I wrote in my code.   #
#   * To learn more about Werkzeug, I watched tutorials on Flask      #
#     and Werkzeug.                                                   #
#   * I also used the Python SQLite3 library instead of the           #
#     CS50 library, which I learned by watching some tutorials.       #
#                                                                     #
#######################################################################


from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import os
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

def get_db():
    db = sqlite3.connect('amazon_clone.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()

    # Drop existing tables
    db.execute('DROP TABLE IF EXISTS cart')
    db.execute('DROP TABLE IF EXISTS orders')
    db.execute('DROP TABLE IF EXISTS order_items')
    db.execute('DROP TABLE IF EXISTS reviews')
    db.execute('DROP TABLE IF EXISTS products')
    db.execute('DROP TABLE IF EXISTS users')

    # Create tables
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        manufacturer TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT NOT NULL,
        release_date DATE NOT NULL
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
        author TEXT NOT NULL,
        body TEXT NOT NULL,
        release_date DATE NOT NULL,
        release_time TIME NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        order_date DATETIME NOT NULL,
        status TEXT NOT NULL,
        total_amount REAL NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price_at_time REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')

    db.commit()

def sync_products():
    db = get_db()

    # List of expected products with columns in correct order (name, manufacturer, price, description, release_date)
    expected_products = [
        # Name, Manufacturer, Price, Description, Release Date
        ("Apple AirPods Pro (2nd Generation)", "Apple", 21250, "Active noise cancellation, spatial audio, and Adaptive Transparency. Comfortable and secure fit.", "2022-09-23"),
        ("Samsung Galaxy S23 Ultra", "Samsung", 100200, "6.8-inch Dynamic AMOLED display, Snapdragon 8 Gen 2, 200MP camera, 5000mAh battery.", "2023-02-01"),
        ("Sony WH-1000XM5 Wireless Headphones", "Sony", 29750, "Industry-leading noise cancellation with a sleek, comfortable design.", "2022-05-20"),
        ("GoPro HERO11 Black", "GoPro", 34000, "5.3K video resolution, hyper-smooth stabilization, waterproof design for all adventures.", "2022-09-15"),
        ("Bose QuietComfort 45 Headphones", "Bose", 27200, "Superior noise cancellation, plush comfort, and rich audio for music and calls.", "2021-09-23"),
        ("Apple Watch Series 8", "Apple", 127500, "Advanced health tracking, crash detection, and always-on display.", "2022-09-16"),
        ("Lenovo ThinkPad X1 Carbon (9th Gen)", "Lenovo", 127500, "Lightweight business laptop with Intel Core i7, 16GB RAM, and 512GB SSD.", "2021-06-01"),
        ("Microsoft Surface Pro 9", "Microsoft", 85000, "13-inch 2-in-1 laptop/tablet, Intel Core i5, 8GB RAM, 128GB SSD.", "2022-10-25"),
        ("DJI Mini 3 Pro Drone", "DJI", 64600, "4K HDR video, 48MP camera, intelligent flight modes, ultra-portable design.", "2022-05-10"),
        ("Amazon Echo Show 8 (2nd Gen)", "Amazon", 11050, "8-inch smart display with Alexa, video calling, streaming, and smart home control.", "2021-06-01"),
        ("NVIDIA GeForce RTX 3080 Graphics Card", "NVIDIA", 68000, "10GB GDDR6X memory, ray tracing, and DLSS for top-tier gaming performance.", "2020-09-17"),
        ("Kindle Paperwhite (11th Gen)", "Amazon", 12000, "6.8-inch screen, adjustable warm light, waterproof design for reading anywhere.", "2021-09-20"),
        ("HP Envy x360 15.6 inch Laptop", "HP", 76500, "15.6-inch touch screen, AMD Ryzen 5, 8GB RAM, and 512GB SSD.", "2021-01-01"),
        ("Razer DeathAdder V2 Pro Wireless Gaming Mouse", "Razer",11050 , "Ultra-precise sensor, customizable RGB lighting, and long battery life.", "2020-06-01"),
        ("Oculus Quest 2 VR Headset", "Meta", 25500, "Standalone VR headset with a 64GB storage option and no PC required.", "2020-10-13"),
        ("Breville BES870XL Barista Express Espresso Machine", "Breville", 59500, "Stainless steel espresso machine with built-in conical burr grinder and steam wand.", "2019-01-01"),
        ("Dyson V15 Detect Cordless Vacuum Cleaner", "Dyson", 76500, "Laser illumination, powerful suction, and anti-tangle technology for deep cleaning.", "2021-03-25"),
        ("Instant Pot Duo 7-in-1 Electric Pressure Cooker", "Instant Pot", 7650, "Combines 7 appliances into one—pressure cooker, slow cooker, rice cooker, steamer, sauté pan, yogurt maker, and more.", "2021-04-01"),
        ("Ninja BN701 Professional Plus Blender", "Ninja", 10200, "1400-peak-watt motor for smoothies, frozen drinks, and food processing.", "2020-10-01"),
        ("Serta Perfect Sleeper Elite Mattress", "Serta", 76500, "Memory foam, innerspring mattress designed for pressure relief and a restful sleep.", "2020-01-01"),
        ("The Silent Patient by Alex Michaelides", "Celadon Books", 1275, "A psychological thriller about a woman who shoots her husband and then refuses to speak.", "2019-02-05"),
        ("Atomic Habits by James Clear", "Avery", 1020, "A guide to building good habits and breaking bad ones, backed by scientific research.", "2018-10-16"),
        ("The Midnight Library by Matt Haig", "Viking", 1445, "A novel about the infinite possibilities of life and the second chances we might wish for.", "2020-08-13"),
        ("Becoming by Michelle Obama", "Crown Publishing Group", 1530, "A memoir by the former First Lady of the United States, exploring her life journey.", "2018-11-13"),
        ("Where the Crawdads Sing by Delia Owens", "G.P. Putnam's Sons", 1190, "A compelling mystery about a girl raised alone in the wild marshes of North Carolina.", "2018-08-14"),
        ("Amazon Gift Card - $50", "Amazon", 4250, "A gift card with a balance of $50, redeemable on Amazon for a wide range of products.", "2022-01-01"),
        ("iTunes Gift Card - $25", "Apple", 2125, "A $25 gift card for iTunes, perfect for music, movies, and apps on Apple devices.", "2021-02-01"),
        ("Google Play Gift Card - $20", "Google", 1700, "A $20 gift card for use in the Google Play Store, applicable for apps, games, movies, and books.", "2021-03-01"),
        ("Starbucks Gift Card - $10", "Starbucks", 850, "A $10 gift card redeemable for Starbucks coffee, beverages, and food items.", "2022-01-01"),
        ("Spotify Premium Subscription (1 month)", "Spotify", 840, "A one-month Spotify Premium subscription, ad-free listening, and offline music.", "2022-01-01")
    ]

    # Get current products from database
    current_products = db.execute('SELECT name, manufacturer, price, description, release_date FROM products').fetchall()

    # Convert to sets for comparison (using name as unique identifier)
    current_names = {product[0] for product in current_products}
    expected_names = {product[0] for product in expected_products}


    if current_names != expected_names:
        # Clear existing products and insert new ones
        db.execute('DELETE FROM products')
        db.executemany('INSERT INTO products (name, manufacturer, price, description, release_date) VALUES (?, ?, ?, ?, ?)', expected_products)
        db.commit()

def is_logged_in():
    return 'user_id' in session

def validate_address(address, city, state, zip_code):
    # Validate ZIP code
    indian_states = [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 
    'Chhattisgarh', 'Goa', 'Gujarat', 'Haryana', 
    'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 
    'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 
    'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 
    'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 
    'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
    'Andaman and Nicobar Islands', 'Chandigarh', 
    'Dadra and Nagar Haveli and Daman and Diu', 'Delhi', 
    'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 
    'Puducherry'
    ]

    # Validate PIN code (Indian postal code)
    if not re.match(r'^\d{6}$', zip_code):
        return False, "Invalid PIN code format. Please enter a 6-digit PIN code"

    # Validate state code
    if state.upper() not in indian_states:
        return False, "Invalid state code. Please use standard state codes (e.g., MH for Maharashtra)"

    # Basic address validation
    if len(address.strip()) < 5:
        return False, "Address is too short"

    # Basic city validation
    if not city.strip() or len(city) < 2:
        return False, "Invalid city name"

    return True, "Valid address"


def validate_card_expiration(expiration):
    try:
        if not re.match(r'^(0[1-9]|1[0-2])\/([0-9]{2})$', expiration):
            return False, "Invalid expiration format (use MM/YY)"

        month, year = map(int, expiration.split('/'))
        exp_date = datetime(2000 + year, month, 1)
        if exp_date <= datetime.now():
            return False, "Card has expired"

        return True, "Valid expiration date"
    except:
        return False, "Invalid expiration date"

@app.route('/')
def landing():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('landing.html')

@app.route('/home')
def home():
    db = get_db()
    products = db.execute('''
        SELECT p.*,
               COALESCE(AVG(r.rating), 0) as avg_rating,
               COUNT(r.id) as review_count
        FROM products p
        LEFT JOIN reviews r ON p.id = r.product_id
        GROUP BY p.id
        ORDER BY p.release_date DESC
    ''').fetchall()
    return render_template('home.html', products=products)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long')
            return redirect(url_for('register'))

        db = get_db()
        try:
            db.execute('INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)',
                      [first_name, last_name, email, generate_password_hash(password)])
            db.commit()

            # Get the newly created user
            user = db.execute('SELECT * FROM users WHERE email = ?', [email]).fetchone()

            # Automatically log them in
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_name'] = f"{user['first_name']} {user['last_name']}"
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            session.permanent = True  # Make session permanent

            flash(f'Welcome, {first_name}! Your account has been created.')
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            flash('Email already exists')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', [email]).fetchone()

        if user and check_password_hash(user['password'], password):
            # Store user info in session
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_name'] = f"{user['first_name']} {user['last_name']}"
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            session.permanent = True  # Make session permanent
            flash(f'Welcome back, {user["first_name"]}!')
            return redirect(url_for('home'))

        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/category/<category>')
def category(category):
    return f'Category: {category}'

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    db = get_db()
    product = db.execute(
        'SELECT p.*, '
        'COALESCE((SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.id), 0) as review_count, '
        'COALESCE((SELECT AVG(CAST(rating AS FLOAT)) FROM reviews r WHERE r.product_id = p.id), 0.0) as avg_rating '
        'FROM products p WHERE p.id = ?',
        (product_id,)
    ).fetchone()


    # Get all reviews for the product
    reviews = db.execute(
        'SELECT r.*, r.body as body, r.author as author, '
        'r.release_date, r.rating '
        'FROM reviews r '
        'WHERE r.product_id = ? '
        'ORDER BY r.release_date DESC, r.release_time DESC',
        (product_id,)
    ).fetchall()

    return render_template('product_detail.html', product=dict(product), reviews=reviews)

@app.route('/product/<int:product_id>/add_review', methods=['POST'])
def add_review(product_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))

    rating = request.form.get('rating')
    body = request.form.get('comment')  # Getting 'comment' from form but using as 'body' in DB

    if not rating or not body:
        flash('Both rating and review text are required')
        return redirect(url_for('product_detail', product_id=product_id))

    try:
        db = get_db()
        # Get user info
        user = db.execute(
            'SELECT first_name, last_name FROM users WHERE id = ?',
            (session['user_id'],)
        ).fetchone()

        author = f"{user['first_name']} {user['last_name']}"

        # Insert review
        db.execute(
            'INSERT INTO reviews (product_id, rating, author, body, release_date, release_time) VALUES (?, ?, ?, ?, date("now"), time("now"))',
            (product_id, rating, author, body)
        )
        db.commit()
        flash('Review added successfully!')
    except sqlite3.Error as e:
        flash(f'Error adding review: {str(e)}')
        print(f"Database error: {e}")

    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    db = get_db()
    products = db.execute('''
        SELECT p.*,
               COALESCE(AVG(r.rating), 0) as avg_rating,
               COUNT(r.id) as review_count
        FROM products p
        LEFT JOIN reviews r ON p.id = r.product_id
        WHERE p.name LIKE ? OR p.manufacturer LIKE ? OR p.description LIKE ?
        GROUP BY p.id
        ORDER BY p.release_date DESC
    ''', [f'%{query}%', f'%{query}%', f'%{query}%']).fetchall()
    return render_template('home.html', products=products, search_query=query)

@app.route('/add_to_cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash('Please login first')
        return redirect(url_for('login'))

    db = get_db()
    try:
        # Add item to cart
        db.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)',
                  [session['user_id'], product_id])
        db.commit()
        flash('Added to cart!')
    except Exception as e:
        print(f"Error: {str(e)}")
        flash('Error adding to cart')
        return redirect(url_for('product_detail', product_id=product_id))

    # If buy_now is set, clear any other items from cart and go to checkout
    if request.method == 'POST' and request.form.get('buy_now'):
        try:
            # Remove all other items from cart
            db.execute('DELETE FROM cart WHERE user_id = ? AND product_id != ?',
                      [session['user_id'], product_id])
            db.commit()
            return redirect(url_for('checkout'))
        except Exception as e:
            print(f"Error clearing cart: {str(e)}")
            flash('Error processing buy now')

    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cart_items = db.execute('''
        SELECT c.id as cart_item_id, c.quantity,
               p.id as product_id, p.name, p.price, p.manufacturer
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', [session['user_id']]).fetchall()

    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/remove_from_cart/<int:item_id>')
def remove_from_cart(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    try:
        # First verify that this cart item belongs to the current user
        cart_item = db.execute('''
            SELECT * FROM cart
            WHERE id = ? AND user_id = ?
        ''', [item_id, session['user_id']]).fetchone()

        if cart_item:
            db.execute('DELETE FROM cart WHERE id = ?', [item_id])
            db.commit()
            flash('Item removed from cart')
        else:
            flash('Item not found in cart')
    except:
        flash('Failed to remove item from cart')

    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cart_items = db.execute('''
        SELECT c.*, p.name, p.price, p.manufacturer
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', [session['user_id']]).fetchall()

    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cart_items = db.execute('''
        SELECT p.id, p.name, p.price, c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', [session['user_id']]).fetchall()

    if not cart_items:
        flash('Your cart is empty')
        return redirect(url_for('cart'))

    # Validate form data
    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    zip_code = request.form.get('zip', '').strip()
    expiration = request.form.get('cc-expiration', '').strip()

    # Validate address
    is_valid_address, address_msg = validate_address(address, city, state, zip_code)
    if not is_valid_address:
        flash(address_msg)
        return redirect(url_for('checkout'))

    # Validate card expiration
    is_valid_exp, exp_msg = validate_card_expiration(expiration)
    if not is_valid_exp:
        flash(exp_msg)
        return redirect(url_for('checkout'))

    # Calculate total amount
    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)

    # Format shipping address
    shipping_address = f"{address}, {city}, {state}, {zip_code}"

    try:
        # Create order
        db.execute('''
            INSERT INTO orders (user_id, order_date, total_amount, shipping_address, status)
            VALUES (?, datetime('now'), ?, ?, 'On its way')
        ''', [session['user_id'], total_amount, shipping_address])

        # Get the order id
        order_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Add order items
        for item in cart_items:
            db.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
                VALUES (?, ?, ?, ?)
            ''', [order_id, item['id'], item['quantity'], item['price']])

        # Clear cart
        db.execute('DELETE FROM cart WHERE user_id = ?', [session['user_id']])
        db.commit()

        flash('Order placed successfully!')
        return redirect(url_for('orders'))

    except sqlite3.Error as e:
        db.rollback()
        flash('Failed to place order. Please try again.')
        return redirect(url_for('cart'))

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    # Get all orders with their items
    orders = db.execute('''
        SELECT o.*, COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.user_id = ?
        GROUP BY o.id
        ORDER BY o.order_date DESC
    ''', [session['user_id']]).fetchall()

    return render_template('orders.html', orders=orders)

@app.route('/order/<int:order_id>')
def order_detail(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    # Get order details
    order = db.execute('''
        SELECT * FROM orders WHERE id = ? AND user_id = ?
    ''', [order_id, session['user_id']]).fetchone()

    if not order:
        flash('Order not found')
        return redirect(url_for('orders'))

    # Get order items with product details
    items = db.execute('''
        SELECT oi.*, p.name, p.manufacturer
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    ''', [order_id]).fetchall()

    return render_template('order_detail.html', order=order, items=items)


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Here you would typically handle the contact form submission
        # For now, we'll just show a success message
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

if __name__ == '__main__':
    init_db()  # Initialize database tables
    sync_products()  # Sync products if needed
    app.run(debug=True)
