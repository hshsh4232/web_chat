import os
import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_migrate import Migrate
from dotenv import load_dotenv # Добавлено для .env

from models import db, User, Message
from forms import LoginForm, RegistrationForm, ProfileUpdateForm, MessageForm

load_dotenv() # Загрузка переменных из .env файла

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
MEDIA_FOLDER = os.path.join(UPLOAD_FOLDER, 'media')
BG_FOLDER = os.path.join(UPLOAD_FOLDER, 'backgrounds')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AVATAR_FOLDER, exist_ok=True)
os.makedirs(MEDIA_FOLDER, exist_ok=True)
os.makedirs(BG_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS_AVATAR = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXTENSIONS_MEDIA = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'mp3', 'wav', 'ogg', 'pdf', 'txt'}
ALLOWED_EXTENSIONS_BG = {'png', 'jpg', 'jpeg', 'gif'}

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = UPLOAD_FOLDER
    AVATAR_FOLDER = AVATAR_FOLDER
    MEDIA_FOLDER = MEDIA_FOLDER
    BG_FOLDER = BG_FOLDER
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."
login_manager.login_message_category = "info"
socketio = SocketIO(app, cors_allowed_origins="*")

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_upload(file, folder, allowed_extensions_set):
    if file and allowed_file(file.filename, allowed_extensions_set):
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{timestamp}_{current_user.id}.{ext}")
        save_path = os.path.join(folder, filename)
        try:
            file.save(save_path)
            relative_folder = os.path.relpath(folder, app.config['UPLOAD_FOLDER'])
            return os.path.join('uploads', relative_folder, filename).replace("\\", "/")
        except Exception as e:
            app.logger.error(f"Failed to save file {filename}: {e}")
            return None
    return None

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя пользователя или пароль.', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'Добро пожаловать, {user.username}!', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))
    return render_template('login.html', title='Вход', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Убрали email=form.email.data
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Поздравляем, вы успешно зарегистрированы!', 'success')
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/')
@app.route('/index')
@login_required
def index():
    message_form = MessageForm()
    messages = Message.query.order_by(Message.timestamp.asc()).limit(100).all()
    return render_template('index.html', title='Чат', messages=messages, form=message_form, user=current_user)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Убрали current_user.email из аргументов формы
    form = ProfileUpdateForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        # current_user.email = form.email.data # УДАЛЕНО

        if form.avatar.data:
            avatar_path = save_upload(form.avatar.data, app.config['AVATAR_FOLDER'], ALLOWED_EXTENSIONS_AVATAR)
            if avatar_path:
                current_user.avatar = avatar_path
            else:
                 flash('Ошибка загрузки аватара. Неверный тип файла?', 'danger')

        if form.bg_image.data:
             bg_path = save_upload(form.bg_image.data, app.config['BG_FOLDER'], ALLOWED_EXTENSIONS_BG)
             if bg_path:
                 current_user.bg_image = bg_path
             else:
                 flash('Ошибка загрузки фона. Неверный тип файла?', 'danger')

        if form.bg_opacity.data is not None:
             current_user.bg_opacity = form.bg_opacity.data

        try:
            db.session.commit()
            flash('Ваш профиль обновлен!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка обновления профиля: {e}', 'danger')

        return redirect(url_for('profile'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        # form.email.data = current_user.email # УДАЛЕНО
        form.bg_opacity.data = current_user.bg_opacity

    avatar_url = url_for('static', filename=current_user.avatar) if current_user.avatar else url_for('static', filename='uploads/avatars/default.jpg')
    return render_template('profile.html', title='Профиль', form=form, avatar_url=avatar_url)


@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        print(f'Client connected: {current_user.username} ({request.sid})')
    else:
        print('Anonymous client tried to connect, disconnecting.')
        return False

@socketio.on('disconnect')
def handle_disconnect():
     if current_user.is_authenticated:
        print(f'Client disconnected: {current_user.username} ({request.sid})')

@socketio.on('send_message')
def handle_send_message(data):
    if not current_user.is_authenticated:
        return

    text = data.get('message')

    if not text:
         print("Empty message received, ignoring.")
         return

    try:
        msg = Message(sender_id=current_user.id, body=text, content_type='text')
        db.session.add(msg)
        db.session.commit()

        message_data = {
            'id': msg.id,
            'username': current_user.username,
            'avatar': url_for('static', filename=current_user.avatar if current_user.avatar else 'uploads/avatars/default.jpg'),
            'body': msg.body,
            'content_type': msg.content_type,
            'media_url': None,
            'timestamp': msg.timestamp.isoformat() + "Z",
            'user_id': current_user.id
        }
        emit('new_message', message_data, broadcast=True)
        print(f"Broadcasted message from {current_user.username}: {text}")

    except Exception as e:
        db.session.rollback()
        print(f"Error saving/broadcasting message: {e}")
        emit('message_error', {'error': 'Could not send message.'}, room=request.sid)


@app.route('/send_message_post', methods=['POST'])
@login_required
def send_message_post():
    form = MessageForm()

    if form.validate_on_submit():
        text = form.message.data
        media_file = form.media.data
        media_saved_path = None
        content_type = 'text'

        if media_file:
            ext = media_file.filename.rsplit('.', 1)[1].lower()
            if ext in {'png', 'jpg', 'jpeg', 'gif'}:
                content_type = 'image'
                media_saved_path = save_upload(media_file, app.config['MEDIA_FOLDER'], ALLOWED_EXTENSIONS_MEDIA)
            elif ext in {'mp4', 'mov', 'avi'}:
                 content_type = 'video'
                 media_saved_path = save_upload(media_file, app.config['MEDIA_FOLDER'], ALLOWED_EXTENSIONS_MEDIA)
            elif ext in {'mp3', 'wav', 'ogg'}:
                 content_type = 'audio'
                 media_saved_path = save_upload(media_file, app.config['MEDIA_FOLDER'], ALLOWED_EXTENSIONS_MEDIA)
            else:
                 content_type = 'file'
                 media_saved_path = save_upload(media_file, app.config['MEDIA_FOLDER'], ALLOWED_EXTENSIONS_MEDIA)

            if not media_saved_path:
                flash('Ошибка загрузки медиафайла. Неверный тип или размер?', 'danger')
                return jsonify({'status': 'error', 'message': 'Media upload failed'}), 400

        if text or media_saved_path:
            try:
                msg = Message(
                    sender_id=current_user.id,
                    body=text if text else None,
                    media_filename=media_saved_path,
                    content_type=content_type
                )
                db.session.add(msg)
                db.session.commit()

                media_full_url = url_for('static', filename=media_saved_path, _external=False) if media_saved_path else None
                message_data = {
                    'id': msg.id,
                    'username': current_user.username,
                    'avatar': url_for('static', filename=current_user.avatar if current_user.avatar else 'uploads/avatars/default.jpg'),
                    'body': msg.body,
                    'content_type': msg.content_type,
                    'media_url': media_full_url,
                    'media_filename_orig': secure_filename(media_file.filename) if media_file else None,
                    'timestamp': msg.timestamp.isoformat() + "Z",
                    'user_id': current_user.id
                }
                socketio.emit('new_message', message_data, broadcast=True)
                print(f"Saved and broadcasted message ID {msg.id} from {current_user.username}")
                return jsonify({'status': 'success', 'message': message_data})

            except Exception as e:
                db.session.rollback()
                print(f"Error saving message from POST: {e}")
                flash('Ошибка отправки сообщения.', 'danger')
                return jsonify({'status': 'error', 'message': 'Could not save message'}), 500
        else:
             flash('Нужно ввести сообщение или прикрепить файл.', 'warning')
             return jsonify({'status': 'error', 'message': 'No content provided'}), 400

    else:
        errors = form.errors
        print(f"Form validation failed: {errors}")
        flash(f"Ошибка валидации формы: {errors}", 'danger')
        return jsonify({'status': 'error', 'message': 'Form validation failed', 'errors': errors}), 400


@app.context_processor
def inject_current_time():
    return {'now': datetime.datetime.utcnow}

@app.cli.command("init-db")
def init_db():
    """Create database tables.""" # Оставил комментарий здесь, т.к. это docstring для команды flask
    # Обернул db.create_all() в блок with app.app_context() для правильного контекста
    with app.app_context():
         db.create_all()
    print("Initialized the database.")

if __name__ == '__main__':
    print("Starting Flask-SocketIO server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)