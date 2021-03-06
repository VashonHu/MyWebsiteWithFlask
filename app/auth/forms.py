# This Python file uses the following encoding: utf-8

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp
from ..models import User
from flask_login import current_user


class LoginForm(FlaskForm):
    email = StringField(u'邮件', validators=[DataRequired(), Length(3, 64), Email()] )
    password = PasswordField(u'密码', validators=[DataRequired()])
    remember_me = BooleanField(u'保持登录')
    submit = SubmitField(u'登录')


class RegistrationForm(FlaskForm):
    email = StringField(u'邮件', validators=[DataRequired(), Length(1, 64), Email()])
    # username = StringField(u'昵称', validators=[DataRequired(), Length(4, 64),
    #                                           Regexp('^[A-Za-z][A-Za-z0-9_]*$', 0,
    #                                                  u'昵称只能包含英文字母，数字和下划线')])

    username = StringField(u'昵称', validators=[
        DataRequired(), Length(4, 64), Regexp('^[A-Za-z][A-Za-z0-9_]', 0, u'昵称只能包含英文字母，数字和下划线')])

    password = PasswordField(u'密码', validators=[
        DataRequired(), EqualTo('password2', message='两次输入的密码必须相同')])
    password2 = PasswordField(u'确认密码', validators=[DataRequired()])
    submit = SubmitField(u'注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮件地址已经被使用！')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u'昵称已经被占用！')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(u'旧密码', validators=[DataRequired()])
    password = PasswordField(u'新密码', validators=[
        DataRequired(), EqualTo('password2', message=u'两次输入的密码必须相同')])
    password2 = PasswordField(u'确认密码', validators=[DataRequired()])
    submit = SubmitField(u'修改密码')


class ChangeEmailForm(FlaskForm):
    password = PasswordField(u'密码', validators=[DataRequired()])
    new_email = StringField(u'新邮件地址', validators=[DataRequired()])
    submit = SubmitField(u'修改邮箱')

    def validate_new_email(self, field):
        u = User.query.filter_by(email=field.data).first()
        if u and u.id != current_user.id:
            raise ValidationError(u'邮件地址已经被使用！')


class ResetPassword(FlaskForm):
    email = StringField(u'邮件', validators=[DataRequired(), Length(3, 64), Email()])
    submit = SubmitField(u'发送邮件用以重置密码')


class PasswordResetForm(FlaskForm):
    email = StringField(u'邮箱地址', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField(u'新密码', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField(u'确认密码', validators=[DataRequired()])
    submit = SubmitField(u'重置密码')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(u'邮箱地址不存在')
