# This Python file uses the following encoding: utf-8

from flask import render_template,redirect, url_for, abort, flash, request, current_app, make_response
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, QuestionForm, CommentForm, AnswerForm
from .. import db
from ..models import User, Role, Permission, Question, Comment, Answer, Vote
from flask_login import login_required, current_user
from ..decorators import admin_required, permission_required
from flask_sqlalchemy import  get_debug_queries
import sys

# if current_user.is_authenticated:
    #     show_followed = bool(request.cookies.get('show_followed', ' '))
    # if show_followed:
    #     query = current_user.followed_questions
    # else:
    #     query = Question.query


@main.route('/', methods=['GET', 'POST'])
def index():
    query_questions = None
    if current_user.is_authenticated and current_user.followers.count() > 0:
        query_questions = current_user.followed_questions
    else:
        query_questions = Question.query
    page = request.args.get('page', 1, type=int)
    pagination_questions = query_questions.order_by(Question.timestamp.desc()).paginate(
        page, per_page=20, error_out=False)
    questions = pagination_questions.items
    return render_template('index.html', questions=questions,
                           pagination_questions=pagination_questions,
                           Answer=Answer, row=2)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    questions = user.questions.order_by(Question.timestamp.desc()).all()
    answers = user.answers.order_by(Answer.timestamp.desc()).all()
    admin = User.query.filter_by(email=current_app.config['FLASK_MAIL_ADMIN']).first()
    return render_template('user.html', user=user, questions=questions,
                           admin=admin, answers=answers, Answer=Answer, row=0)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        return redirect(url_for('.user', username=current_user.name))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit_profile_admin/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash("The account's profile has been updated.")
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role
    form.name.data = user.name
    form.location = user.location
    form.about_me = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/question/<int:id>', methods=['GET', 'POST'])
def question(id):
    question = Question.query.get_or_404(id)
    form = AnswerForm()
    if form.validate_on_submit():
        answer = Answer(
            body=form.body.data,
            question=question,
            author=current_user._get_current_object())
        db.session.add(answer)
        db.session.commit()
        flash(u'您的回答已提交。')
        return redirect(url_for('.question', id=question.id, page=-1))#id
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (question.answers.count() - 1) \
               / current_app.config['FLASK_ANSWERS_PER_PAGE'] - 1
    pagination = question.answers.order_by(Answer.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASK_ANSWERS_PER_PAGE'],
        error_out=False)
    answers = pagination.items
    return render_template('question.html', questions=[question], form=form,
                           answers=answers, pagination=pagination, row=sys.maxint, Answer=Answer)


@main.route('/edit_question/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_question(id):
    question = Question.query.get_or_404(id)
    if current_user != question.author \
            and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = QuestionForm()
    if form.validate_on_submit():
        question.title = form.title.data
        question.body = form.body.data
        db.session.add(question)
        db.session.commit()
        flash(u'这个问题已经被更新。')
        return redirect(url_for('question', id=question.id))
    form.title.data = question.title
    form.body.data = question.body
    return render_template('edit_question.html', form=form)


@main.route('/edit_answer/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_answer(id):
    answer = Answer.query.get_or_404(id)
    if current_user != answer.author \
            and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = AnswerForm()
    if form.validate_on_submit():
        answer.body = form.body.data
        db.session.add(answer)
        db.session.commit()
        flash(u'这个回答已经被更新。')
        return redirect(url_for('.answer', id=answer.id))
    form.body.data = answer.body
    return render_template('edit_answer.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user!')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user!')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are already unfollow this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are now unfollow %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user!')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASK_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user!')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASK_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)

#
# @main.route('/all')
# @login_required
# def show_all():
#     resp = make_response(redirect(url_for('.index')))
#     resp.set_cookie('show_followed', '', max_age=30*24*60*60)
#     return resp
#
#
# @main.route('/followed')
# @login_required
# def show_followed():
#     resp = make_response(redirect(url_for('.index')))
#     resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
#     return resp
#


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASK_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASK_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %f\nContext: %s\n' % \
                (query.statement, query.parameters, query.duration, query.context))
    return response


@main.route('/square')
def square():
    query_questions = Question.query
    page = request.args.get('page', 1, type=int)
    pagination_questions = query_questions.order_by(Question.timestamp.desc()).paginate(
        page, per_page=20, error_out=False)
    questions = pagination_questions.items
    return render_template('square.html', questions=questions,
                           pagination_questions=pagination_questions,
                           Answer=Answer, row=2)


@main.route('/post_question', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE_ARTICLES)
def post_question():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(title=form.title.data,
                            body=form.body.data,
                            author=current_user._get_current_object())
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('.question', id=question.id))
    return render_template('post_question.html', form=form)


@main.route('/vote/<int:id>')
@login_required
def vote(id):
    # answer = Answer.query.get_or_404(id)
    vote = Vote(answer=id,
                author=current_user._get_current_object())
    db.session.add(vote)
    db.session.commit()
    return redirect(request.args.get('next') or  url_for('.index'))

