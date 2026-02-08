#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import traceback
from datetime import datetime, timedelta
from io import BytesIO
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    send_file, jsonify, send_from_directory
)
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models import db, User, Company, Product, Purchase, Sale, StockMovement

# ============================================
# INITIALIZATION
# ============================================

app = Flask(__name__, 
            template_folder='app/templates',
            static_folder='app/static')
app.config.from_object(Config)

# Ensure directories exist
os.makedirs('database', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('reports', exist_ok=True)
os.makedirs('backups', exist_ok=True)
os.makedirs('app/templates', exist_ok=True)
os.makedirs('app/static/css', exist_ok=True)
os.makedirs('app/static/js', exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================
# HELPER FUNCTIONS
# ============================================

def init_database():
    """Initialize database with default data"""
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            
            # Create admin user if not exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin_user = User(
                    username='admin',
                    password=generate_password_hash('admin123'),
                    is_admin=True,
                    last_login=datetime.now()
                )
                db.session.add(admin_user)
                print("Created admin user: admin/admin123")
            
            # Create default company if not exists
            company = Company.query.first()
            if not company:
                default_company = Company(
                    name='Perusahaan FIFO',
                    address='Jl. Contoh No. 123',
                    phone='081234567890',
                    email='info@perusahaan.com'
                )
                db.session.add(default_company)
                print("Created default company")
            
            db.session.commit()
            print("Database initialized successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing database: {str(e)}")
            traceback.print_exc()

# ============================================
# CONTEXT PROCESSORS
# ============================================

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.context_processor
def inject_stats():
    if current_user.is_authenticated:
        try:
            total_products = Product.query.count()
            total_purchases = Purchase.query.count()
            total_sales = Sale.query.count()
            
            # Calculate stock value
            stock_value = 0
            products = Product.query.all()
            for product in products:
                stock_value += product.get_stock_value()
            
            return {
                'total_products': total_products,
                'total_purchases': total_purchases,
                'total_sales': total_sales,
                'stock_value': stock_value
            }
        except:
            return {}
    return {}

# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            user.last_login = datetime.now()
            db.session.commit()
            
            login_user(user, remember=remember)
            flash('Login berhasil!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Username atau password salah!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

# ============================================
# MAIN ROUTES
# ============================================

@app.route('/')
@login_required
def index():
    """Dashboard"""
    # Get recent activities
    try:
        recent_purchases = Purchase.query.order_by(Purchase.date.desc()).limit(5).all()
        recent_sales = Sale.query.order_by(Sale.date.desc()).limit(5).all()
        low_stock_products = Product.query.filter(
            Product.stock <= Product.min_stock
        ).order_by(Product.stock.asc()).limit(5).all()
        
        return render_template('index.html',
                             recent_purchases=recent_purchases,
                             recent_sales=recent_sales,
                             low_stock_products=low_stock_products)
    except Exception as e:
        return render_template('index.html')

@app.route('/products')
@login_required
def products():
    """Products list"""
    products_list = Product.query.order_by(Product.name).all()
    return render_template('products.html', products=products_list)

@app.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add product"""
    if request.method == 'POST':
        try:
            code = request.form.get('code')
            name = request.form.get('name')
            unit = request.form.get('unit')
            min_stock = float(request.form.get('min_stock', 0))
            
            if not code or not name:
                flash('Kode dan nama produk harus diisi!', 'error')
                return redirect(url_for('add_product'))
            
            # Check if code exists
            existing = Product.query.filter_by(code=code).first()
            if existing:
                flash('Kode produk sudah digunakan!', 'error')
                return redirect(url_for('add_product'))
            
            product = Product(
                code=code,
                name=name,
                unit=unit,
                min_stock=min_stock
            )
            
            db.session.add(product)
            db.session.commit()
            
            flash(f'Produk {name} berhasil ditambahkan!', 'success')
            return redirect(url_for('products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('product_form.html', product=None)

@app.route('/product/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    """Edit product"""
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            product.code = request.form.get('code')
            product.name = request.form.get('name')
            product.unit = request.form.get('unit')
            product.min_stock = float(request.form.get('min_stock', 0))
            
            db.session.commit()
            flash('Produk berhasil diupdate!', 'success')
            return redirect(url_for('products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('product_form.html', product=product)

@app.route('/product/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    """Delete product"""
    if not current_user.is_admin:
        flash('Akses ditolak! Hanya admin yang bisa menghapus produk.', 'error')
        return redirect(url_for('products'))
    
    try:
        product = Product.query.get_or_404(id)
        
        # Check if product has transactions
        has_purchases = Purchase.query.filter_by(product_id=id).first()
        has_sales = Sale.query.filter_by(product_id=id).first()
        
        if has_purchases or has_sales:
            flash('Tidak bisa menghapus produk yang sudah memiliki transaksi!', 'error')
            return redirect(url_for('products'))
        
        db.session.delete(product)
        db.session.commit()
        
        flash('Produk berhasil dihapus!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('products'))

@app.route('/purchases')
@login_required
def purchases():
    """Purchases list"""
    purchases_list = Purchase.query.order_by(Purchase.date.desc()).all()
    products = Product.query.order_by(Product.name).all()
    return render_template('purchases.html', purchases=purchases_list, products=products)

@app.route('/purchase/add', methods=['POST'])
@login_required
def add_purchase():
    """Add purchase"""
    try:
        product_id = request.form.get('product_id', type=int)
        quantity = float(request.form.get('quantity', 0))
        price = float(request.form.get('price', 0))
        
        if not product_id or quantity <= 0 or price <= 0:
            flash('Data tidak valid!', 'error')
            return redirect(url_for('purchases'))
        
        product = Product.query.get_or_404(product_id)
        
        # Create purchase
        purchase = Purchase(
            product_id=product_id,
            quantity=quantity,
            price=price,
            remaining_quantity=quantity,
            date=datetime.now(),
            user_id=current_user.id
        )
        
        # Update product stock
        product.stock += quantity
        
        # Create stock movement
        movement = StockMovement(
            product_id=product_id,
            purchase_id=purchase.id,
            quantity=quantity,
            price=price,
            date=datetime.now(),
            type='purchase'
        )
        
        db.session.add(purchase)
        db.session.add(movement)
        db.session.commit()
        
        flash('Pembelian berhasil ditambahkan!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('purchases'))

@app.route('/purchase/delete/<int:id>', methods=['POST'])
@login_required
def delete_purchase(id):
    """Delete purchase"""
    try:
        purchase = Purchase.query.get_or_404(id)
        product = Product.query.get(purchase.product_id)
        
        # Update product stock
        product.stock -= purchase.quantity
        
        # Delete related stock movements
        StockMovement.query.filter_by(purchase_id=id).delete()
        
        db.session.delete(purchase)
        db.session.commit()
        
        flash('Pembelian berhasil dihapus!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('purchases'))

@app.route('/sales')
@login_required
def sales():
    """Sales list"""
    sales_list = Sale.query.order_by(Sale.date.desc()).all()
    products = Product.query.filter(Product.stock > 0).order_by(Product.name).all()
    return render_template('sales.html', sales=sales_list, products=products)

@app.route('/sale/add', methods=['POST'])
@login_required
def add_sale():
    """Add sale with FIFO"""
    try:
        product_id = request.form.get('product_id', type=int)
        quantity = float(request.form.get('quantity', 0))
        selling_price = float(request.form.get('selling_price', 0))
        
        if not product_id or quantity <= 0 or selling_price <= 0:
            flash('Data tidak valid!', 'error')
            return redirect(url_for('sales'))
        
        product = Product.query.get_or_404(product_id)
        
        # Check stock
        if product.stock < quantity:
            flash(f'Stok tidak cukup! Stok tersedia: {product.stock}', 'error')
            return redirect(url_for('sales'))
        
        # Get purchases for FIFO (oldest first)
        purchases = Purchase.query.filter_by(product_id=product_id)\
            .filter(Purchase.remaining_quantity > 0)\
            .order_by(Purchase.date.asc()).all()
        
        remaining_qty = quantity
        total_cost = 0
        movements = []
        
        for purchase in purchases:
            if remaining_qty <= 0:
                break
            
            qty_to_take = min(purchase.remaining_quantity, remaining_qty)
            cost = qty_to_take * purchase.price
            total_cost += cost
            
            purchase.remaining_quantity -= qty_to_take
            
            movement = StockMovement(
                product_id=product_id,
                purchase_id=purchase.id,
                quantity=-qty_to_take,
                price=purchase.price,
                date=datetime.now(),
                type='sale'
            )
            movements.append(movement)
            
            remaining_qty -= qty_to_take
        
        if remaining_qty > 0:
            flash('Error dalam perhitungan FIFO!', 'error')
            return redirect(url_for('sales'))
        
        avg_cost = total_cost / quantity if quantity > 0 else 0
        
        # Create sale
        sale = Sale(
            product_id=product_id,
            quantity=quantity,
            selling_price=selling_price,
            cost_price=avg_cost,
            date=datetime.now(),
            user_id=current_user.id
        )
        
        # Update product stock
        product.stock -= quantity
        
        db.session.add(sale)
        for movement in movements:
            db.session.add(movement)
        
        db.session.commit()
        
        flash('Penjualan berhasil diproses!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('sales'))

@app.route('/sale/delete/<int:id>', methods=['POST'])
@login_required
def delete_sale(id):
    """Delete sale"""
    try:
        sale = Sale.query.get_or_404(id)
        product = Product.query.get(sale.product_id)
        
        # Update product stock
        product.stock += sale.quantity
        
        # Delete related movements
        StockMovement.query.filter_by(
            product_id=sale.product_id,
            type='sale'
        ).delete()
        
        db.session.delete(sale)
        db.session.commit()
        
        flash('Penjualan berhasil dibatalkan!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('sales'))

# ============================================
# REPORTS ROUTES
# ============================================

@app.route('/reports')
@login_required
def reports():
    """Reports page"""
    # Get some data for the reports page
    try:
        today = datetime.now().date()
        
        # Today's sales
        today_sales = Sale.query.filter(
            db.func.date(Sale.date) == today
        ).all()
        today_sales_total = sum(sale.quantity * sale.selling_price for sale in today_sales)
        today_profit = sum((sale.selling_price - sale.cost_price) * sale.quantity for sale in today_sales)
        
        # Monthly stats
        first_day = today.replace(day=1)
        monthly_sales = Sale.query.filter(Sale.date >= first_day).all()
        monthly_sales_total = sum(sale.quantity * sale.selling_price for sale in monthly_sales)
        monthly_profit = sum((sale.selling_price - sale.cost_price) * sale.quantity for sale in monthly_sales)
        
        return render_template('reports.html',
                             today_sales_total=today_sales_total,
                             today_profit=today_profit,
                             monthly_sales_total=monthly_sales_total,
                             monthly_profit=monthly_profit)
    except Exception as e:
        flash(f'Error memuat laporan: {str(e)}', 'error')
        return render_template('reports.html')

@app.route('/report/profit_loss')
@login_required
def profit_loss_report():
    """Generate profit loss report"""
    try:
        period = request.args.get('period', 'monthly')
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Parse date
        date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Set date range based on period
        if period == 'daily':
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == 'monthly':
            start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = date.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:  # yearly
            start_date = date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = date.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        
        # Get company info
        company = Company.query.first()
        
        # Get data
        purchases = Purchase.query.filter(Purchase.date.between(start_date, end_date)).all()
        sales = Sale.query.filter(Sale.date.between(start_date, end_date)).all()
        
        # Calculate totals
        total_purchase = sum(p.quantity * p.price for p in purchases)
        total_sales = sum(s.quantity * s.selling_price for s in sales)
        total_cost = sum(s.quantity * s.cost_price for s in sales)
        gross_profit = total_sales - total_cost
        
        return render_template('profit_loss_report.html',
                             period=period,
                             date=date,
                             start_date=start_date,
                             end_date=end_date,
                             total_purchase=total_purchase,
                             total_sales=total_sales,
                             total_cost=total_cost,
                             gross_profit=gross_profit,
                             company=company)
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('reports'))

# ============================================
# COMPANY SETTINGS
# ============================================

@app.route('/company', methods=['GET', 'POST'])
@login_required
def company_settings():
    """Company settings"""
    company = Company.query.first()
    
    if request.method == 'POST' and current_user.is_admin:
        try:
            company.name = request.form.get('name')
            company.address = request.form.get('address')
            company.phone = request.form.get('phone')
            company.email = request.form.get('email')
            
            db.session.commit()
            flash('Data perusahaan berhasil diupdate!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('company.html', company=company)

# ============================================
# IMPORT PAGE
# ============================================

@app.route('/import')
@login_required
def import_data():
    """Import data"""
    return render_template('import.html')

# ============================================
# USER MANAGEMENT
# ============================================

@app.route('/users')
@login_required
def users():
    """User management"""
    if not current_user.is_admin:
        flash('Akses ditolak!', 'error')
        return redirect(url_for('index'))
    
    users_list = User.query.all()
    return render_template('users.html', users=users_list)

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register new user"""
    if not current_user.is_admin:
        flash('Akses ditolak!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            is_admin = request.form.get('is_admin') == 'true'
            
            if not username or not password:
                flash('Username dan password harus diisi!', 'error')
                return redirect(url_for('register'))
            
            # Check if username exists
            existing = User.query.filter_by(username=username).first()
            if existing:
                flash('Username sudah digunakan!', 'error')
                return redirect(url_for('register'))
            
            user = User(
                username=username,
                password=generate_password_hash(password),
                is_admin=is_admin
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'User {username} berhasil ditambahkan!', 'success')
            return redirect(url_for('users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('register.html')

# ============================================
# STATIC FILE ROUTES
# ============================================

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('app/static', filename)

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

# ============================================
# STARTUP
# ============================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("FIFO STOCK MANAGEMENT SYSTEM")
    print("="*60)
    
    # Initialize database
    init_database()
    
    print(f"\nServer running on: http://localhost:5000")
    print(f"Login dengan: username='admin', password='admin123'")
    print("\nTekan Ctrl+C untuk menghentikan server")
    print("="*60 + "\n")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\nServer dihentikan oleh pengguna")
    except Exception as e:
        print(f"\n\nError: {str(e)}")
