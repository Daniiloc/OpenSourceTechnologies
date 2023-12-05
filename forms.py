from wtforms import StringField, SubmitField, PasswordField, EmailField, IntegerField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, InputRequired, EqualTo, Length


class SignUpForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(), Length(min=4, max=128)])
    email = EmailField('Почта', validators=[DataRequired(), Email(message='Неправильный адрес почты')])
    password = PasswordField('Пароль', validators=[InputRequired(), DataRequired(), Length(min=8, max=64)])
    confirm = PasswordField('Повторите пароль',
                            validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать')])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired(), Email(message='Неправильный адрес почты')])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class LoginTwoFactorForm(FlaskForm):
    code = IntegerField('Код подтверждения', validators=[DataRequired()])
    submit = SubmitField('Войти')


class ForgotPasswordForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired(), Email(message='Неправильный адрес почты')])
    submit = SubmitField('Отправить письмо для смены пароля')


class ChangePassword(FlaskForm):
    code = IntegerField('Код подтверждения', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[InputRequired(), DataRequired(), Length(min=8, max=64)])
    confirm = PasswordField('Повторите пароль',
                            validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать')])
    submit = SubmitField('Изменить пароль')
