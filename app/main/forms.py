# This Python file uses the following encoding: utf-8

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, ValidationError, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp
from ..models import User, Role
from flask_pagedown.fields import PageDownField


# class NameForm(FlaskForm):
#     name = StringField('你的名字：', validators=[DataRequired()])
#     submit = SubmitField('提交')


class QuestionForm(FlaskForm):
    title = StringField(u'请简要描述你的问题：', validators=[DataRequired()])
    body = PageDownField(u"详述问题：", validators=[DataRequired()])
    submit = SubmitField(u'提交')


class AnswerForm(FlaskForm):
    body = PageDownField(u'回答：', validators=[DataRequired()])
    submit = SubmitField(u'提交')


class EditProfileForm(FlaskForm):
    name = StringField(u'真实姓名：', validators=[Length(0, 64)])
    location = StringField(u'地址：', validators=[Length(0, 64)])
    about_me = TextAreaField(u'关于我：')
    submit = SubmitField(u'提交')


class EditProfileAdminForm(FlaskForm):
    email = StringField(u'电子邮件', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField(u'昵称', validators=[DataRequired(), Length(4, 64),
                                             Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                    u'注意：昵称只能包含英文字母，数字和下划线')])
    confirmed = BooleanField(u'邮件验证')
    role = SelectField(u'角色', coerce=int)
    name = StringField(u'角色名', validators=[Length(0, 64)])
    location = StringField(u'地址', validators=[Length(0, 64)])
    about_me = TextAreaField(u'关于我')
    submit = SubmitField(u'提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)\
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if self.user.email != field.data\
                and User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮件地址已经被注册！')

    def validate_username(self, field):
        if self.user.username != field.data \
                and User.query.filter_by(username=field.data).first():
            raise ValidationError(u'昵称已经被注册！')


class CommentForm(FlaskForm):
    body = StringField('', validators=[DataRequired])
    submit = SubmitField(u'提交')
