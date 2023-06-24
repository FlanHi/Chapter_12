from app import app, db
from app.models import User, Post
from flask_login import login_user, logout_user, login_required, current_user
from flask import render_template, flash, redirect, url_for, request
from app.forms import RegisterForm, LoginForm, EditProfileForm, PostForm
from datetime import datetime

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form=EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        return redirect(url_for('profile', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template(
        'edit_profile.html',
        title='Edit Profile',
        form=form
    )

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/<username>/profile')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.paginate(
        page=page,
        per_page=app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    next_url = url_for('profile', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('profile', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template(
        'profile.html',
        title='Profile',
        user=user,
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url
    )



@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    elif request.method == 'POST' and not form.validate_on_submit():
        flash('An error has occured')
        return redirect('/register')
    return render_template('register.html', title='Register', form=form)


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page,
        per_page=app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    current_user_posts = current_user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page,
        per_page=app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    user_next_url = url_for('index', page=current_user_posts.next_num) \
        if current_user_posts.has_next else None
    user_prev_url = url_for('index', page=current_user_posts.prev_num) \
        if current_user_posts.has_prev else None
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None

    return render_template(
        'index.html',
        title='Index',
        form=form,
        posts=posts.items,
        current_user_posts = current_user_posts.items,
        next_url=next_url,
        prev_url=prev_url,
        user_next_url=user_next_url,
        user_prev_url=user_prev_url
        
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    elif request.method == 'POST' and not form.validate_on_submit():
        flash('An error has occured')
        return redirect('/login')
    return render_template('login.html', title='Log In', form=form)