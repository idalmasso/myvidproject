from app.videoapp import bp
from app.videoapp.forms import AddTorrentForm
from flask import url_for, request, render_template, send_from_directory, current_app, flash,redirect
from flask_login import login_required, current_user
from app.video import Video
import os

import base64


@bp.route('/')
def index():
    return render_template('index.html', title='Home')


@bp.route('/videolist')
@login_required
def videolist():
    Video.update_video_torrents_info()
    page = request.args.get('page', 1, type=int)
    videos = Video.get_list_videos(page, current_app.config['VIDEO_PER_PAGE'])
    prev_url = url_for('videoapp.videolist', page=videos.prev) if videos.has_prev else None
    next_url = url_for('videoapp.videolist', page=videos.next) if videos.has_next else None
    return render_template('videoapp/videolist.html', title='Videos',
                           prev_url=prev_url, next_url=next_url, videos=videos.videos)


@bp.route('/video/<id>')
@login_required
def video(id):
    video = Video.get_video(id)
    if video.torrent_status == 'completed':
        filename = 'http://127.0.0.1:8000/videoapp/uploads/' + video.id
        return render_template('videoapp/video.html', video=video, title=video.title, filename=filename)
    return redirect(url_for('videoapp.videolist'))


@bp.route('/uploads/<id>')
def send_file(id):
    video = Video.get_video(id)
    if video.torrent_status == 'completed':
        return send_from_directory(current_app.config['FILMS_FOLDER'], video.id+'.mp4')
    return redirect(url_for('videoapp.videolist'))


@bp.route('/video_info/<id>', methods=['GET', 'POST'])
@login_required
def video_info(id):
    video = Video.get_video(id)
    video.update_torrent_info()
    if video is None:
        flash('video with id {} does not exist'.format(id))
        return redirect(url_for('videoapp.videolist'))
    if request.method == 'POST':
        video.try_update_from_imdb()
        return redirect(url_for('videoapp.videolist'))
    else:
        filename = 'http://127.0.0.1:8000/videoapp/uploads/' + video.id
        return render_template('videoapp/video.html', video=video, title=video.title, filename=filename)


@bp.route('/add_torrent', methods=['GET', 'POST'])
@login_required
def add_torrent():
    form = AddTorrentForm()
    if form.validate_on_submit():

        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            Video.add_video(form.title.data, base64.b64encode(file.read()).decode('utf-8'))
            return redirect(url_for('videoapp.videolist'))
        else:
            flash('no secure filename')
            return redirect(url_for(request.url))
    return render_template('videoapp/add_torrent.html', form=form, title='Add torrent')


@bp.route('/delete_video/<id>', methods=['POST'])
@login_required
def delete_video(id):
    if current_user.admin:
        Video.get_video(id).remove_video()
    return redirect(url_for('videoapp.videolist'))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
