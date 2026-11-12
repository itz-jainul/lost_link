from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('Item', backref='reporter', lazy=True)
    claims = db.relationship('Claim', backref='claimant', lazy=True)
    messages_sent = db.relationship('Message', backref='sender', lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(80))
    location = db.Column(db.String(200))
    date_lost_found = db.Column(db.Date)
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)
    item_type = db.Column(db.String(20), nullable=False)  # 'missing' or 'found'
    image_filename = db.Column(db.String(300))
    status = db.Column(db.String(30), default='active')  # active/approved/claimed/removed
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    contact_details = db.Column(db.String(300), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    claims = db.relationship('Claim', backref='item', lazy=True)

class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    claimant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.Text)
    proof = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    conversation = db.relationship('Conversation', uselist=False, backref='claim')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    to_contact = db.Column(db.String(200), nullable=False)
    channel = db.Column(db.String(20))
    subject = db.Column(db.String(200))
    body = db.Column(db.Text)
    sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey('claim.id'), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    claimant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade="all, delete-orphan")
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='conversations_reporter')
    claimant = db.relationship('User', foreign_keys=[claimant_id], backref='conversations_claimant')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
