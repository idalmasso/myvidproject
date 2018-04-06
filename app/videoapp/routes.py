from app.videoapp import bp
from app.videoapp.forms import AddTorrentForm
from flask import url_for, request, render_template, send_from_directory, current_app,flash,redirect
from flask_login import login_required
from app.video import Video
import os
import subprocess


@bp.route('/')
def index():
    return render_template('index.html', title='Home')


@bp.route('/videolist')
@login_required
def videolist():
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
    filename = 'http://127.0.0.1:5000/videoapp/uploads/' + video.id

    return render_template('videoapp/video.html', video=video, title='Video', filename=filename)


@bp.route('/uploads/<id>')
def send_file(id):
    video = Video.get_video(id)
    if not os.path.exists(os.path.join(os.path.dirname(video.file_path),video.id+'.mp4')):
        subprocess.run(['ffmpeg', '-i', video.file_path, '-c:v','libvpx','-c:a','libvorbis',
                                                    os.path.join(os.path.dirname(video.file_path),video.id+'.mp4')])
    return send_from_directory(os.path.dirname(video.file_path), video.id+'.mp4')


@bp.route('/video_info/<id>', methods=['GET', 'POST'])
@login_required
def video_info(id):
    video = Video.get_video(id)
    if video is None:
        flash('video with id {} does not exist'.format(id))
        return redirect(url_for('videoapp.videolist'))
    if request.method == 'POST':
        video.try_update_from_imdb()
        return redirect(url_for('videoapp.videolist'))
    else:
        filename = 'http://127.0.0.1:5000/videoapp/uploads/' + video.id
        return render_template('videoapp/video_info.html', video=video, title=video.title, filename=filename)


@bp.route('/add_torrent', methods=['GET', 'POST'])
@login_required
def add_torrent():
    form = AddTorrentForm()
    if form.validate_on_submit():
        return redirect(url_for('videoapp.videolist'))
    return render_template('videoapp/add_torrent.html', form=form, title='Add torrent')
