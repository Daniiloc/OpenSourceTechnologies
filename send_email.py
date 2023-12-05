import smtplib

from settings import *
from email.mime.text import MIMEText


def send_email(to_email, theme, content):
    theme_list = ['battle_result', 'confirm_login', 'change_password']

    title = ''
    start = ''
    if theme == theme_list[0]:
        title = 'Результат боя'
        start = 'Результаты вашего боя.'
    elif theme == theme_list[1]:
        title = 'Подтверждение входа'
        start = 'Для подтверждения входа на сайт введите код в поле авторизации:'
    elif theme == theme_list[2]:
        title = 'Изменение пароля'
        start = ('Вы получили это письмо так как запросили изменение пароля. '
                 'Вы можете изменить его введя код подтверждения:')
    text = start + ' ' + str(content)
    message = MIMEText(text)
    message['Subject'] = title
    message['From'] = email_config['sender']
    message['To'] = to_email
    sender = email_config['sender']
    password = email_config['password']

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, to_email, message.as_string())

    server.quit()
