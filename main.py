import json
import requests
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Email, Length, DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

db = SQLAlchemy()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Secret!'
bootstrap = Bootstrap(app)
app.app_context().push()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
admin = Admin(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///final.db'
db.init_app(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(20))
    watchlist = db.relationship('Watchlist', backref='user')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=20)])
    remember = BooleanField('remember me')


class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=20)])

class UpdateAccountForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[DataRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[DataRequired(), Length(min=8, max=20)])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                return 'That username is taken. Please choose a different one.'

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                return 'That email is taken. Please choose a different one.'


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    imdbid = db.Column(db.String, unique=True, nullable=False)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.String)
    released = db.Column(db.String)
    genre = db.Column(db.String)
    director = db.Column(db.String)
    actors = db.Column(db.String)
    plot = db.Column(db.String)
    poster = db.Column(db.String)
    imdbrating = db.Column(db.String)
    boxoffice = db.Column(db.String)
    runtime = db.Column(db.String)
    trailers = db.relationship('Trailer', backref='movies')


class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    imdbid = db.Column(db.String, unique=True, nullable=False)
    title = db.Column(db.String, unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Trailer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trailer = db.Column(db.String)
    name = db.Column(db.String)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'))


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    films = Movies.query.order_by(Movies.id).all()
    return render_template('main.html', films=films)


@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    user = User.query.order_by(User.id).all()
    if id == 2:
        return render_template('admin.html', user=user)
    else:
        return redirect(url_for('index'))


@app.route('/result', methods=['GET', "POST"])
def result():
    print(request)
    print(request.method)
    print(request.form)
    search = request.form['search']
    url = "https://movie-database-alternative.p.rapidapi.com/"
    headers = {
        "X-RapidAPI-Key": "9109307733msh75b286e988495fap1fd289jsn7c67c07eaea0",
        "X-RapidAPI-Host": "movie-database-alternative.p.rapidapi.com"
    }
    querystring1 = {"s": f"{search}", "r": "json", "page": "1"}
    response1 = requests.request("GET", url, headers=headers, params=querystring1)
    r = response1.json()
    imdbid = r['Search'][0]['imdbID']

    if Movies.query.filter_by(imdbid=imdbid).first() is None:
        # error page if written movie doesn't exist in API
        querystring2 = {"r": "json", "i": f"{imdbid}", 'plot': 'full'}
        response2 = requests.request("GET", url, headers=headers, params=querystring2)
        if response2.status_code == 404:
            return render_template('errorpage.html')
        b = response2.json()
        title = b['Title']
        year = b['Year']
        imdbid = b['imdbID']
        released = b['Released']
        genre = b['Genre']
        runtime = b['Runtime']
        director = b['Director']
        actors = b['Actors']
        plot = b['Plot']
        poster = b['Poster']
        imdbrating = b['imdbRating']
        boxoffice = b['BoxOffice']
        url2 = f'https://www.googleapis.com/youtube/v3/search?key=AIzaSyA2XbqrZZvrYGqT2Tnb14acYDBfw-wwD_c&q={title}trailer&part=snippet'
        a = requests.get(url2)
        response3 = a.json()
        trailer = response3['items'][0]['id']['videoId']
        movie = Movies(imdbid=imdbid, title=title, year=year, released=released, genre=genre, director=director,
                       actors=actors, plot=plot, poster=poster, imdbrating=imdbrating, boxoffice=boxoffice,
                       runtime=runtime)
        db.session.add(movie)
        db.session.commit()
        max = Trailer(trailer=trailer, name=title, movie_id=movie.id)
        db.session.add(max)
        db.session.commit()

    film = Movies.query.filter_by(imdbid=imdbid).first()
    trailer2 = Trailer.query.filter_by(movie_id=film.id).first()
    return render_template('result.html', title=film.title, year=film.year, released=film.released, genre=film.genre,
                           director=film.director, actors=film.actors, plot=film.plot, poster=film.poster,
                           imdbrating=film.imdbrating, boxoffice=film.boxoffice, runtime=film.runtime,
                           trailer=trailer2.trailer)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('index'))

        return '<h1>Invalid username or password</h1>'

    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()

    if form.validate_on_submit():
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('signup.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.password = form.password.data
        db.session.commit()
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.password.data = current_user.password
    return render_template('account.html', title='Account',
                            form=form)


if __name__ == '__main__':
    app.run(debug=True, host="localhost", port=4000)
