# This Python file uses the following encoding: utf-8

from flask import render_template, url_for, redirect, request, flash, current_app
from . import auth
from ..models import User
from .forms import LoginForm, RegistrationForm, ChangePasswordForm
from flask_login import login_user, login_required, logout_user, current_user
from .. import db
from ..email import send_mail


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash(u'无效的用户名或密码！')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'你现在已经登出。')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.genarate_confirmation_taken()
        if current_app.config['FLASK_MAIL_ADMIN']:
            send_mail(current_app.config['FLASK_MAIL_ADMIN'],
                      u'确认您的账户', 'auth/email/confirm', user=user, token=token)
        flash(u'A confirmation email has been sent to you by email.')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash(u'您已经确认您的账户，谢谢！')
    else:
        flash(u'这个链接错误或令牌已经失效！')
    return redirect(url_for('main.index'))


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.genarate_confirmation_taken()
    if current_app.config['FLASK_MAIL_ADMIN']:
        send_mail(current_app.config['FLASK_MAIL_ADMIN'],
                  'Confirm Your Account', 'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(request.args.get('next') or url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password):
            current_user.password = form.password
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been changed!')
            return redirect(request.args.get('next') or url_for('main.index'))
        else:
            flash('Invalid password!')
    return render_template('auth/change_password.html', form=form)


@auth.route('/.password_reset_request', methods=['GET', 'POST'])
def password_reset_request():
    pass


@auth.route('/change_email_request', methods=['GET', 'POST'])
def change_email_request():
    pass
