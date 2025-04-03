from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField, FloatField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length, Optional, NumberRange
# Убрали Email валидатор, т.к. поле email удалено
from models import User
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    # email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)]) # УДАЛЕНО
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать.')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Это имя пользователя уже занято.')

    # def validate_email(self, email): # УДАЛЕНО
    #     user = User.query.filter_by(email=email.data).first()
    #     if user is not None:
    #         raise ValidationError('Этот email уже используется.')

class ProfileUpdateForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    # email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)]) # УДАЛЕНО
    avatar = FileField('Сменить аватар', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Разрешены только изображения!')
    ])
    bg_image = FileField('Сменить фон чата', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Разрешены только изображения!')
    ])
    bg_opacity = FloatField('Прозрачность фона (0.0 - 1.0)', validators=[
        Optional(),
        NumberRange(min=0.0, max=1.0, message='Значение должно быть от 0.0 до 1.0')
    ])
    submit = SubmitField('Обновить профиль')

    # Убрали original_email из конструктора и валидации
    def __init__(self, original_username, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        # self.original_email = original_email # УДАЛЕНО

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Это имя пользователя уже занято.')

    # def validate_email(self, email): # УДАЛЕНО
    #      if email.data != self.original_email:
    #         user = User.query.filter_by(email=email.data).first()
    #         if user is not None:
    #             raise ValidationError('Этот email уже используется.')

class MessageForm(FlaskForm):
    message = StringField('Сообщение', validators=[Optional(), Length(max=500)])
    media = FileField('Прикрепить файл', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'mp3', 'wav', 'ogg', 'pdf', 'txt'], 'Неподдерживаемый тип файла!')
        ])
    submit = SubmitField('Отправить')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        if not self.message.data and not self.media.has_file():
            msg = 'Нужно ввести сообщение или прикрепить файл.'
            self.message.errors.append(msg)
            self.media.errors.append(msg)
            return False
        return True