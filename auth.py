import secrets

from models import *
from models import Users
from send_email import send_email
from flask_login import login_user, current_user, logout_user, login_required
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from forms import SignUpForm, LoginForm, LoginTwoFactorForm, ForgotPasswordForm, ChangePassword


auth = Blueprint('auth', __name__, template_folder='templates')


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('hello'))

    form = SignUpForm()
    if form.validate_on_submit():
        user = Users.query.filter(Users.email == form.email.data).first()
        if user:
            flash('Этот email уже занят', 'error')
            return render_template('sign_up.html', form=form)

        user = Users(name=form.name.data,
                     email=form.email.data,
                     password=form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('auth.login'))
        except Exception:
            db.session.rollback()
            flash('Не удалось зарегистрировать вас. Попробуйте снова позже.', 'error')
    return render_template('sign_up.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('hello'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter(Users.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            code = random.randint(100000000, 999999999)
            print('CODE FOR LOGIN:', code)
            session['data_login'] = {'email': user.email, 'code': code}
            send_email(to_email=user.email,
                       theme='confirm_login',
                       content=code)
            return redirect(url_for('auth.confirm_login'))
        flash('Неверная почта или пароль', 'error')
    return render_template('login.html', form=form)


@auth.route('/confirm-login', methods=['GET', 'POST'])
def confirm_login():
    if current_user.is_authenticated:
        return redirect(url_for('hello'))

    form = LoginTwoFactorForm()
    if 'data_login' not in session:
        return redirect(url_for('auth.login'))
    if form.validate_on_submit():
        data_login = session['data_login']
        user = Users.query.filter(Users.email == data_login['email']).first()
        if user:
            if data_login['code'] == form.code.data:
                cache.clear()
                login_user(user)
                return redirect(url_for('hello'))
            else:
                flash('Неверный код подтверждения', 'error')
        else:
            flash('Unexpected error.', 'error')
    return render_template('login_two_factor.html', form=form)


@auth.route('/login-yandex-id')
def login_yandex_id():
    cache.clear()
    if current_user.is_authenticated:
        return redirect(url_for('hello'))
    return redirect(
        f"{YANDEX_ID_URL}?response_type=code&client_id={YANDEX_ID_CLIENT_ID}&redirect_uri={YANDEX_ID_CALLBACK_URI}")


@auth.route('/login-yandex-id/callback')
def login_yandex_id_callback():
    cache.clear()
    if current_user.is_authenticated:
        return redirect(url_for('hello'))

    code = request.args.get('code', None)
    data_request_token = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': YANDEX_ID_CLIENT_ID,
        'client_secret': YANDEX_ID_CLIENT_SECRET,
        'redirect_uri': YANDEX_ID_CALLBACK_URI
    }
    response_token = requests.post(YANDEX_ID_TOKEN_URL, data=data_request_token)

    if response_token.status_code != 200:
        flash('Error occurred on the Yandex ID server side.', 'error')
        return render_template('login.html', form=LoginForm())

    token_json = response_token.json()  # access_token, expires_in, refresh_token, token_type

    # get info about user from Yandex ID
    headers = {'Authorization': f"OAuth {token_json['access_token']}"}
    response_user_info = requests.get('https://login.yandex.ru/info?format=json', headers=headers)

    if response_user_info.status_code != 200:
        flash('Error occurred on the Yandex ID server side.', 'error')
        return render_template('login.html', form=LoginForm())

    user_info_json = response_user_info.json()
    user_info = {'id': user_info_json.get('id'),
                 'name': user_info_json.get('real_name', None),
                 'email': user_info_json.get('default_email', None)}

    # checking user and login
    user = Users.query.filter(Users.email == user_info['email']).first()
    if user:
        # updating name from Yandex ID
        if user.name != user_info['name']:
            user.name = user_info['name']
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print("ERROR DB: User update name failed\n", e)
                flash('Failed to update username.', 'error')

        login_user(user)
        return redirect(url_for('hello'))
    else:
        user = Users(name=user_info['name'],
                     email=user_info['email'],
                     password=secrets.token_urlsafe(128))
        try:
            db.session.add(user)
            db.session.commit()

            login_user(user)
            return redirect(url_for('hello'))
        except Exception:
            db.session.rollback()
            flash('Непредвиденная ошибка. Попробуйте зарегистрироваться через сайт', 'error')
    return render_template('login.html', form=LoginForm())


@auth.route('/log-out')
@login_required
def log_out():
    if 'data_login' in session:
        session.pop('data_login')
    if 'data_to_change_password' in session:
        session.pop('data_to_change_password')
    logout_user()
    return redirect(url_for('hello'))


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('hello'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = Users.query.filter(Users.email == form.email.data).first()
        if user:
            code = random.randint(100000000, 999999999)
            print('CODE FOR CHANGE PASSWORD:', code)
            session['data_to_change_password'] = {'email': user.email, 'code': code}

            send_email(to_email=user.email,
                       theme='change_password',
                       content=code)

            return redirect(url_for('auth.change_password'))
        flash('Почта не привязана к какому-либо аккаунту.', 'error')
    return render_template('forgot_password.html', form=form)


@auth.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if current_user.is_authenticated:
        return redirect(url_for('hello'))

    form = ChangePassword()
    if form.validate_on_submit():
        data_to_change_password = session['data_to_change_password']
        if form.code.data == data_to_change_password['code']:
            user = Users.query.filter(Users.email == data_to_change_password['email']).first()
            if user:
                user.password = user.get_password_hash(form.password.data)
                try:
                    db.session.commit()
                    return redirect(url_for('auth.login'))
                except Exception:
                    db.session.rollback()
                    flash('Не получилось изменить пароль. Попробуйте позже.', 'error')
        flash('Неверный код', 'error')
    return render_template('change_password.html', form=form)
