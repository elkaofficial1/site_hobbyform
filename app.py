from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import random
import string
from flask_mail import Mail, Message
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from PIL import Image
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
# Настройки для почты VK.com
app.config['MAIL_SERVER'] = 'smtp.mail.ru'
app.config['MAIL_PORT'] = 587  # Изменяем порт на 587
app.config['MAIL_USE_TLS'] = True  # Включаем TLS
app.config['MAIL_USE_SSL'] = False  # Отключаем SSL
app.config['MAIL_USERNAME'] = 'mark_novikov_06@vk.com'
app.config['MAIL_PASSWORD'] = 'ваш-пароль'  # Замените на ваш пароль от почты
app.config['MAIL_DEFAULT_SENDER'] = 'mark_novikov_06@vk.com'
app.config['MAIL_MAX_EMAILS'] = 5
app.config['MAIL_ASCII_ATTACHMENTS'] = False
app.config['MAIL_DEBUG'] = True

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Telegram Bot configuration
TELEGRAM_BOT_TOKEN = 'YOUR_BOT_TOKEN'  # Замените на ваш токен
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'  # Замените на ваш chat_id

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=True)  # По умолчанию считаем email верифицированным
    city = db.Column(db.String(100))
    preferred_delivery = db.Column(db.String(50))
    orders = db.relationship('Order', backref='customer', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if 'is_verified' not in kwargs:
            self.is_verified = False
        if 'is_admin' not in kwargs:
            self.is_admin = False

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_ru = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    description_ru = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))
    category = db.Column(db.String(50))
    stock = db.Column(db.Integer, default=0)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_ordered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    payment_details = db.Column(db.Text)
    total_amount = db.Column(db.Float, nullable=False)
    delivery_method = db.Column(db.String(50))
    delivery_address = db.Column(db.Text)
    payment_screenshot = db.Column(db.String(200))  # Путь к скриншоту
    payment_confirmed = db.Column(db.Boolean, default=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    # Add relationship to Product
    product = db.relationship('Product', backref='order_items')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Language handling
@app.before_request
def before_request():
    if 'language' not in session:
        session['language'] = 'en'

@app.route('/set_language/<lang>')
def set_language(lang):
    session['language'] = lang
    return redirect(request.referrer or url_for('home'))

# Routes
@app.route('/')
def home():
    return render_template('home.html', language=session['language'])

@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products, language=session['language'])

@app.route('/about')
def about():
    return render_template('about.html', language=session['language'])

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you can add code to send the message via email
        # For now, we'll just flash a success message
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product, language=session['language'])

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    shipping = 5.00 if subtotal > 0 else 0
    total = subtotal + shipping
    return render_template('cart.html', 
                         cart_items=cart_items,
                         subtotal=subtotal,
                         shipping=shipping,
                         total=total,
                         language=session['language'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        
        flash('Invalid email or password' if session['language'] == 'en' else 'Неверный email или пароль')
    return render_template('login.html', language=session['language'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        city = request.form.get('city')
        preferred_delivery = request.form.get('delivery_method')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered' if session['language'] == 'en' else 'Email уже зарегистрирован')
            return redirect(url_for('register'))
        
        try:
            user = User(
                email=email,
                name=name,
                city=city,
                preferred_delivery=preferred_delivery
            )
            user.password_hash = generate_password_hash(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Отправляем приветственное письмо
            if send_welcome_email(user):
                flash('Registration successful! Welcome email sent.' if session['language'] == 'en' else 'Регистрация успешна! Приветственное письмо отправлено.')
            else:
                flash('Registration successful, but we could not send welcome email. Please check your email address.' if session['language'] == 'en' else 'Регистрация успешна, но мы не смогли отправить приветственное письмо. Пожалуйста, проверьте ваш email адрес.')
            
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during registration: {str(e)}")
            flash('An error occurred during registration. Please try again.' if session['language'] == 'en' else 'Произошла ошибка при регистрации. Пожалуйста, попробуйте снова.')
            return redirect(url_for('register'))
    
    return render_template('register.html', language=session['language'])

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id)
        db.session.add(cart_item)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/update_cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    action = request.json.get('action')
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease':
            cart_item.quantity -= 1
            if cart_item.quantity <= 0:
                db.session.delete(cart_item)
        
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 404

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied' if session['language'] == 'en' else 'Доступ запрещен')
        return redirect(url_for('home'))
    products = Product.query.all()
    orders = Order.query.all()
    return render_template('admin/dashboard.html', 
                         products=products, 
                         orders=orders,
                         language=session['language'])

@app.route('/admin/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    if not current_user.is_admin:
        flash('Access denied' if session['language'] == 'en' else 'Доступ запрещен')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        product = Product(
            name=request.form['name'],
            name_ru=request.form['name_ru'],
            description=request.form['description'],
            description_ru=request.form['description_ru'],
            price=float(request.form['price']),
            image_url=request.form['image_url'],
            category=request.form['category'],
            stock=int(request.form['stock']),
            created_by=current_user.id
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully' if session['language'] == 'en' else 'Товар успешно добавлен')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/new_product.html', language=session['language'])

@app.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_admin:
        flash('Access denied' if session['language'] == 'en' else 'Доступ запрещен')
        return redirect(url_for('home'))
    
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.name_ru = request.form['name_ru']
        product.description = request.form['description']
        product.description_ru = request.form['description_ru']
        product.price = float(request.form['price'])
        product.image_url = request.form['image_url']
        product.category = request.form['category']
        product.stock = int(request.form['stock'])
        db.session.commit()
        flash('Product updated successfully' if session['language'] == 'en' else 'Товар успешно обновлен')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_product.html', product=product, language=session['language'])

@app.route('/admin/order/<int:order_id>')
@login_required
def view_order(order_id):
    if not current_user.is_admin:
        flash('Access denied' if session['language'] == 'en' else 'Доступ запрещен')
        return redirect(url_for('home'))
    
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order.html', order=order, language=session['language'])

@app.route('/admin/order/<int:order_id>/update', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    order = Order.query.get_or_404(order_id)
    order.status = request.json.get('status')
    db.session.commit()
    return jsonify({'success': True})

# Payment routes
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
async def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return redirect(url_for('cart'))
    
    if request.method == 'POST':
        delivery_method = request.form.get('delivery_method')
        delivery_address = request.form.get('delivery_address')
        
        # Create order
        order = Order(
            user_id=current_user.id,
            total_amount=sum(item.product.price * item.quantity for item in cart_items),
            payment_details=request.form['payment_details'],
            delivery_method=delivery_method,
            delivery_address=delivery_address
        )
        db.session.add(order)
        
        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order=order,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
        
        # Clear cart
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        
        # Отправляем уведомление в Telegram
        order_message = f"""
Новый заказ #{order.id}
От: {current_user.name} ({current_user.email})
Сумма: {order.total_amount} ₽
Способ доставки: {delivery_method}
Адрес: {delivery_address}
"""
        await send_telegram_notification(order_message)
        
        flash('Order placed successfully' if session['language'] == 'en' else 'Заказ успешно оформлен')
        return redirect(url_for('order_confirmation', order_id=order.id))
    
    return render_template('checkout.html', 
                         cart_items=cart_items,
                         total=sum(item.product.price * item.quantity for item in cart_items),
                         language=session['language'])

@app.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    
    # Load order items with their products
    order.items = OrderItem.query.filter_by(order_id=order.id).all()
    
    return render_template('order_confirmation.html', order=order, language=session['language'])

# Добавляем маршрут для загрузки скриншота оплаты
@app.route('/upload_payment/<int:order_id>', methods=['POST'])
@login_required
async def upload_payment(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    
    if 'payment_screenshot' not in request.files:
        flash('No file uploaded' if session['language'] == 'en' else 'Файл не загружен')
        return redirect(url_for('order_confirmation', order_id=order_id))
    
    file = request.files['payment_screenshot']
    if file.filename == '':
        flash('No file selected' if session['language'] == 'en' else 'Файл не выбран')
        return redirect(url_for('order_confirmation', order_id=order_id))
    
    if file:
        # Сохраняем файл
        filename = f"payment_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join('static', 'payments', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        # Обновляем информацию о заказе
        order.payment_screenshot = filepath
        db.session.commit()
        
        # Отправляем уведомление в Telegram
        message = f"""
Получен скриншот оплаты для заказа #{order.id}
От: {current_user.name} ({current_user.email})
Сумма: {order.total_amount} ₽
"""
        await send_telegram_notification(message, filepath)
        
        flash('Payment screenshot uploaded successfully' if session['language'] == 'en' else 'Скриншот оплаты успешно загружен')
    
    return redirect(url_for('order_confirmation', order_id=order_id))

# Добавляем маршрут для подтверждения оплаты (для админа)
@app.route('/confirm_payment/<int:order_id>', methods=['POST'])
@login_required
async def confirm_payment(order_id):
    if not current_user.is_admin:
        abort(403)
    
    order = Order.query.get_or_404(order_id)
    order.payment_confirmed = True
    order.status = 'processing'
    db.session.commit()
    
    # Отправляем уведомление в Telegram
    message = f"""
Оплата подтверждена для заказа #{order.id}
Подтвердил: {current_user.name}
"""
    await send_telegram_notification(message)
    
    return jsonify({'success': True})

# Create admin user
def create_admin_user():
    with app.app_context():
        admin = User.query.filter_by(email='admin@moldcraft.com').first()
        if not admin:
            admin = User(
                email='admin@moldcraft.com',
                name='Admin',
                is_admin=True,
                is_verified=True,
                city='Moscow',
                preferred_delivery='pickup'
            )
            admin.password_hash = generate_password_hash('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists!")

def send_welcome_email(user):
    try:
        msg = Message('Добро пожаловать в MoldCraft!',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[user.email])
        
        if session['language'] == 'ru':
            msg.body = f'''Здравствуйте, {user.name}!

Добро пожаловать в MoldCraft - ваш магазин премиальных силиконовых форм!

Мы рады, что вы присоединились к нашему сообществу. Теперь вы можете:
- Просматривать наш каталог товаров
- Совершать покупки
- Отслеживать статус заказов
- Получать уведомления о новых поступлениях

Если у вас возникнут вопросы, не стесняйтесь обращаться к нам.

С уважением,
Команда MoldCraft
'''
        else:
            msg.body = f'''Hello, {user.name}!

Welcome to MoldCraft - your premium silicone molds store!

We're glad you've joined our community. Now you can:
- Browse our product catalog
- Make purchases
- Track your orders
- Receive notifications about new arrivals

If you have any questions, feel free to contact us.

Best regards,
MoldCraft Team
'''
        
        print(f"Attempting to send welcome email to {user.email}")
        mail.send(msg)
        print(f"Welcome email sent successfully to {user.email}")
        return True
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        return False

@app.route('/become-admin', methods=['GET', 'POST'])
@login_required
def become_admin():
    if current_user.is_admin:
        flash('You are already an admin' if session['language'] == 'en' else 'Вы уже являетесь администратором')
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        admin_code = request.form.get('admin_code')
        if admin_code == '3470jdhF':
            current_user.is_admin = True
            db.session.commit()
            flash('Congratulations! You are now an admin' if session['language'] == 'en' else 'Поздравляем! Теперь вы администратор')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin code' if session['language'] == 'en' else 'Неверный код администратора')
    
    return render_template('become_admin.html', language=session['language'])

# Функция для отправки уведомлений в Telegram
async def send_telegram_notification(message, photo_path=None):
    try:
        if photo_path:
            with open(photo_path, 'rb') as photo:
                await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=photo, caption=message)
        else:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        return True
    except Exception as e:
        print(f"Error sending Telegram notification: {str(e)}")
        return False

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
        
        # Add sample products if none exist
        if not Product.query.first():
            sample_products = [
                Product(
                    name="Soap Flower Mold",
                    name_ru="Форма для мыла 'Цветок'",
                    description="Beautiful flower-shaped silicone mold for soap making. Perfect for creating decorative soaps.",
                    description_ru="Красивая силиконовая форма в виде цветка для изготовления мыла. Идеально подходит для создания декоративного мыла.",
                    price=15.99,
                    image_url="https://example.com/flower-mold.jpg",
                    category="soap",
                    stock=50,
                    created_by=1
                ),
                Product(
                    name="Chocolate Heart Mold",
                    name_ru="Форма для шоколада 'Сердце'",
                    description="Premium silicone heart mold for chocolate making. Creates perfect heart-shaped chocolates.",
                    description_ru="Премиальная силиконовая форма в виде сердца для изготовления шоколада. Создает идеальные шоколадные сердечки.",
                    price=12.99,
                    image_url="https://example.com/heart-mold.jpg",
                    category="chocolate",
                    stock=75
                ),
                Product(
                    name="Geometric Soap Mold Set",
                    name_ru="Набор геометрических форм для мыла",
                    description="Set of 6 geometric silicone molds for creating modern, minimalist soap designs.",
                    description_ru="Набор из 6 геометрических силиконовых форм для создания современных, минималистичных дизайнов мыла.",
                    price=24.99,
                    image_url="https://example.com/geometric-set.jpg",
                    category="soap",
                    stock=30
                )
            ]
            db.session.add_all(sample_products)
            db.session.commit()
    
    app.run(host='0.0.0.0', port=5000, debug=True) 