from threading import Thread
from flask_mail import Message
from . import mail
from flask import render_template, current_app


def send_async_email(app, msg):
    with app.app_context():
            mail.send(msg)


def send_mail(to, subject, template, **kwargs):
    #app = current_app
    app = current_app._get_current_object()
    msg = Message(subject, sender=app.config['FLASK_MAIL_SENDER'],
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr