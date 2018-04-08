import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, 'configuration.env'))

class Config(object):
    MONGO_HOST = 'localhost'
    MONGO_PORT = 27017
    MONGO_DBNAME = 'video_app_db'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-key-that_cannot-be-guessed'
    VIDEO_PER_PAGE = 20
    FILMS_FOLDER = '/home/ivano/films'
    ALLOWED_EXTENSIONS = set(['torrent'])
    VIDEO_EXTENSIONS = set(['.mkv', '.mp4', '.avi', '.webm'])
    ffmpeg = "ffmpeg"
    ffmpeg_transcode_args = {
        "*": ["-f", "mp4", "-strict", "experimental", "-preset", "ultrafast", "-movflags",
              "frag_keyframe+empty_moov+faststart", "pipe:1"],
        "mp3": ["-f", "mp3", "-codec", "copy", "pipe:1"]}
    
