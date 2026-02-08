from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    purchases = db.relationship('Purchase', backref='user', lazy=True)
    sales = db.relationship('Sale', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default='Perusahaan FIFO')
    address = db.Column(db.Text, default='Jl. Contoh No. 123')
    phone = db.Column(db.String(20), default='081234567890')
    email = db.Column(db.String(100), default='info@perusahaan.com')
    website = db.Column(db.String(100))
    tax_id = db.Column(db.String(20))
    logo = db.Column(db.Text)  # Base64 encoded
    currency = db.Column(db.String(10), default='IDR')
    currency_symbol = db.Column(db.String(5), default='Rp')
    decimal_places = db.Column(db.Integer, default=2)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Company {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), default='pcs')
    stock = db.Column(db.Float, default=0)
    min_stock = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    purchases = db.relationship('Purchase', backref='product', lazy=True)
    sales = db.relationship('Sale', backref='product', lazy=True)
    stock_movements = db.relationship('StockMovement', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.code} - {self.name}>'
    
    def get_stock_value(self):
        """Calculate stock value using FIFO method"""
        try:
            # Get all purchases with remaining quantity
            purchases = Purchase.query.filter_by(product_id=self.id)\
                .filter(Purchase.remaining_quantity > 0)\
                .order_by(Purchase.date.asc()).all()
            
            total_value = 0
            remaining_qty = self.stock
            
            for purchase in purchases:
                if remaining_qty <= 0:
                    break
                
                qty_to_take = min(purchase.remaining_quantity, remaining_qty)
                total_value += qty_to_take * purchase.price
                remaining_qty -= qty_to_take
            
            return total_value
        except:
            return 0
    
    def get_average_price(self):
        """Calculate average purchase price"""
        try:
            purchases = Purchase.query.filter_by(product_id=self.id).all()
            if not purchases:
                return 0
            
            total_qty = sum(p.quantity for p in purchases)
            total_value = sum(p.quantity * p.price for p in purchases)
            
            return total_value / total_qty if total_qty > 0 else 0
        except:
            return 0

class Purchase(db.Model):
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    remaining_quantity = db.Column(db.Float, default=0)  # For FIFO calculation
    date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship
    stock_movements = db.relationship('StockMovement', backref='purchase', lazy=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set initial remaining quantity
        if self.remaining_quantity == 0:
            self.remaining_quantity = self.quantity
    
    def __repr__(self):
        return f'<Purchase {self.id} - Product {self.product_id}>'

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)  # Calculated using FIFO
    date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Sale {self.id} - Product {self.product_id}>'

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=True)
    quantity = db.Column(db.Float, nullable=False)  # Positive for purchase, negative for sale
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    type = db.Column(db.String(10))  # 'purchase' or 'sale'
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<StockMovement {self.type} - Qty: {self.quantity}>'
