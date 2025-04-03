from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    #email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    avatar = db.Column(db.String(128), default='default.jpg')
    bg_image = db.Column(db.String(128), default=None, nullable=True)
    bg_opacity = db.Column(db.Float, default=1.0) # 0.0 to 1.0
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='author', lazy='dynamic')
    # Add relationship for received messages if doing private chats, otherwise room-based is simpler

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    content_type = db.Column(db.String(20), default='text') # 'text', 'image', 'video', 'audio', 'file'
    body = db.Column(db.Text, nullable=True) # For text messages
    media_filename = db.Column(db.String(256), nullable=True) # For media files

    # Add room_id if implementing chat rooms
    # room_id = db.Column(db.Integer, db.ForeignKey('room.id'))

    def __repr__(self):
        return f'<Message {self.id} by {self.sender_id} at {self.timestamp}>'

# Optional: Add Room model if needed
# class Room(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(64), unique=True, nullable=False)
#     messages = db.relationship('Message', backref='room', lazy='dynamic')