from app.authentication import bp
from flask import url_for, request, render_template, redirect, flash
from flask_login import login_required, current_user, login_user, logout_user
from app.authentication.forms import LoginForm,RegistrationForm
from app.usermodel import User
from werkzeug.urls import url_parse


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('videoapp.videolist'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_user(form.username.data)
        if user is None or not user.check_password(form.password.data) or not user.enabled:
            flash('Incorrect user or password')
            return redirect(url_for('videoapp.videolist'))
        login_user(user, form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('videoapp.index')
        return redirect(next_page)
    return render_template('authentication/login.html', title='Login', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('videoapp.index'))


@bp.route('/admin')
@login_required
def admin():
    if current_user.admin and current_user.enabled:
        requests = User.get_list_user_requests()
        users = User.get_list_users()
        return render_template('authentication/admin.html', title='Admin', requests=requests, users=users)
    else:
        return redirect(url_for('videoapp.index'))


@bp.route('/accept_request/<username>', methods=['POST'])
@login_required
def accept_request(username):
    if current_user.admin and current_user.enabled:
        user_request = User.find_user_request(username)
        if user_request is not None:
            User.accept_request(user_request)
            flash('user enabled')
        else:
            flash('user does not exists')
        return redirect(url_for('authentication.admin'))
    else:
        return redirect(url_for('videoapp.index'))


@bp.route('/delete_request/<username>', methods=['POST'])
@login_required
def delete_request(username):
    if current_user.admin and current_user.enabled:
        user_request = User.find_user_request(username)
        if user_request is not None:
            User.delete_request(user_request)
            flash('request deleted')
        else:
            flash('user does not exists')
        return redirect(url_for('authentication.admin'))
    else:
        return redirect(url_for('videoapp.index'))


@bp.route('/enable_user/<username>', methods=['POST'])
@login_required
def enable_user(username):
    if current_user.admin and current_user.enabled:
        user_request = User.find_user(username)
        if user_request is not None:
            user_request.enable()
            flash('user enabled')
        else:
            flash('user does not exists')
        return redirect(url_for('authentication.admin'))
    else:
        return redirect(url_for('videoapp.index'))


@bp.route('/disable_user/<username>', methods=['POST'])
@login_required
def disable_user(username):
    if current_user.admin and current_user.enabled:
        user_request = User.find_user(username)
        if user_request is not None:
            user_request.disable()
            flash('user disabled')
        else:
            flash('user does not exists')
        return redirect(url_for('authentication.admin'))
    else:
        return redirect(url_for('videoapp.index'))


@bp.route('/delete_user/<username>', methods=['POST'])
@login_required
def delete_user(username):
    if current_user.admin and current_user.enabled:
        user_request = User.find_user(username)
        if user_request is not None:
            user_request.delete()
            flash('user deleted')
        else:
            flash('user does not exists')
        return redirect(url_for('authentication.admin'))
    else:
        return redirect(url_for('videoapp.index'))


@bp.route('/registration', methods=['POST', 'GET'])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for('videoapp.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.set_password(form.password.data)
        user.request_registration()
        flash('Registration request registered')
        return redirect(url_for('videoapp.index'))
    return render_template('authentication/registration.html', title='Register', form=form)
