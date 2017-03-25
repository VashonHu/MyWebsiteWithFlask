from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from datetime import datetime
from markdown import markdown
import bleach
from . import log_manager
from flask import url_for
from app.exceptions import ValidationError


class Permission:
    FOLLOW = 0X01
    COMMENT = 0X02
    WRITE_ARTICLES = 0X04
    MODERATE_COMMENTS = 0x8
    ADMINISTER = 0X80


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(64), unique=True, index=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    permission = db.Column(db.Integer)
    default = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permission = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)#Nickname
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(64), unique=True, index=True)
    confirmed = db.Column(db.Boolean, default=False)

    name = db.Column(db.String(64))#real name
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('Question', backref='author', lazy='dynamic')

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    answers = db.relationship('Answer', backref='author', lazy='dynamic')

    votes = db.relationship('Vote', backref='author', lazy='dynamic')

    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASK_MAIL_ADMIN']:
                self.role = Role.query.filter_by(permission=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        self.follow(self)

    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def password(self):
        raise ValueError("password is not a readable attribute!")

    @password.setter
    def password(self, p):
        self.password_hash = generate_password_hash(p)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def genarate_confirmation_taken(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})
        # return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def can(self, permissions):
        return self.role is not None and \
                (self.role.permission & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)
            db.session.commit()

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id()).first()
        if f:
            db.session.delete(f)
            db.session.commit()

    def to_json(self):
        json_user = {
            'url': url_for('api.get_question', id=self.id, _external=True),
            'username': self.username,
            'menber_since': self.menber_since,
            'last_seen': self.last_seen,
            'questions': url_for('api.get_user_questions', id=self.id, _external=True),
            'followed_questions': url_for('api.get_user_followed_questions',
                                      id=self.id, _external=True),
            'question_count': self.questions.count()}
        return json_user

    @staticmethod
    def generate_fake(count=200):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    @property
    def followed_questions(self):
        return Question.query.join(Follow, Follow.followed_id == Question.author_id)\
            .filter(Follow.follower_id == self.id)

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
        db.session.commit()

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer(), primary_key=True)
    body = db.Column(db.Text)
    title = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)
    answers = db.relationship('Answer', backref='question', lazy='dynamic')

    def to_json(self):
        json_question = {
            'url': url_for('api.get_question', id=self.id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id, _external=True),
            'comments': url_for('api.get_question_comments', id=self.id, _external=True),
            'comment_count': self.comments.count()}
        return json_question

    @staticmethod
    def from_json(json_question):
        body = json_question.get('body')
        if body is None or body == '':
            raise ValidationError('question does not have a body')
        return Question(body=body)

    @staticmethod
    def generate_fake(count=1000):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            q = Question(title=forgery_py.lorem_ipsum.sentence(),
                         body=forgery_py.lorem_ipsum.sentence(),
                         timestamp=forgery_py.date.date(True),
                         author=u)
            db.session.add(q)
        db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def top_answers(self, limit_row=1):
        sql = db.text('SELECT questions.id, answers.id, count(votes.id)' +
                      'FROM questions, answers, votes ' +
                      'WHERE questions.id = :val and questions.id \
                      = answers.question_id and answers.id = votes.answer_id \
                      GROUP BY questions.id, answers.id \
                      ORDER BY count(votes.id) DESC \
                      LIMIT :limit_rows')
        result = db.engine.execute(sql, val=self.id, limit_rows=limit_row)
        row1 = []
        row2 = []
        row3 = []
        for row in result:
            row1.append(row[0])
            row2.append(row[1])
            row3.append(row[2])
        return row1, row2, row3

db.event.listen(Question.body, 'set', Question.on_changed_body)


class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    votes = db.relationship('Vote', backref='answer', lazy='dynamic')
    comments = db.relationship('Comment', backref='answer', lazy='dynamic')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em'
                                                             'i', 'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    @staticmethod
    def generate_fake():
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        ques_count = Question.query.count()
        for q in range(ques_count):
            for j in range(randint(1, 10)):
                u = User.query.offset(randint(0, user_count - 1)).first()
                ques = Question.query.get(q)
                a = Answer(body=forgery_py.lorem_ipsum.sentence(),
                           timestamp=forgery_py.date.date(True),
                           author=u,
                           question=ques)
                db.session.add(a)
        db.session.commit()

    def to_json(self):
        json_question = {
            'url': url_for('api.get_answer', id=self.id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id, _external=True),
            'question': url_for('api.get_question', id=self.question_id, _external=True),
            'comments': url_for('api.get_answer_comments', id=self.id, _external=True),
            'comment_count': self.comments.count()}
        return json_question

db.event.listen(Answer.body, 'set', Answer.on_changed_body)


class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Vote %r>' % self.author_id

    @staticmethod
    def generate_fake():
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        answer_count = Question.query.count()
        for a in range(answer_count):
            for j in range(randint(1, 10)):
                u = User.query.offset(randint(0, user_count - 1)).first()
                answer = Answer.query.get(a)
                v = Vote(timestamp=forgery_py.date.date(True),
                         author=u,
                         answer=answer)
                db.session.add(v)
        db.session.commit()


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'))

    @staticmethod
    def generate_fake():
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        answer_count = Question.query.count()
        for i in range(answer_count):
            for j in range(randint(1, 10)):
                u = User.query.offset(randint(0, user_count - 1)).first()
                answer = Answer.query.get(i)
                c = Comment(body=forgery_py.lorem_ipsum.sentence(),
                            timestamp=forgery_py.date.date(True),
                            author=u, answer=answer)
                db.session.add(c)
        db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em'
                        'i', 'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_question = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id, _external=True),
            'answer': url_for('api.get_answer', id=self.question_id, _external=True),}
        return json_question

db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


@log_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)#key

log_manager.anonymous_user = AnonymousUser



