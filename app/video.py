from app import mongo
from flask import current_app
from bson.objectid import ObjectId
import os
from bs4 import BeautifulSoup
import urllib.request
import json
import transmissionrpc
from transmissionrpc.error import TransmissionError
from threading import Thread
import subprocess
import shutil
import time

tc = transmissionrpc.Client('localhost', port=9091)


class Video(object):
    title = ''
    image_path = ''
    file_path = ''

    def __init__(self, video=None):
        if video is not None:
            self.title = video.get('title', '')
            self.image_path = video.get('image_path', None)
            self.file_path = video.get('file_path', None)
            self.description = video.get('summary', None)
            self.rating = video.get('rating', None)
            self.duration = video.get('duration', None)
            self.imdb_id = video.get('imdb_id', None)
            self.image = video.get('image', None)
            self.release_date = video.get('release_date', None)
            self.genre = video.get('genre', None)
            self.actors = video.get('actors', None)
            self.id = str(video.get('_id', ''))
            self.torrent_status = video.get('torrent_status', None)
            self.torrent_id = int(video.get('torrent_id', '-1'))
            self.torrent_progress = video.get('torrent_progress', '0')
            self.torrent_eta = video.get('torrent_eta', '')

    def remove_video(self):
        if self.torrent_id > 0:
            tc.stop_torrent(self.torrent_id)
            tc.remove_torrent(self.torrent_id)
            if self.file_path is not None and os.path.exists(self.file_path + '.part'):
                os.remove(self.file_path + '.part')
        if self.file_path is not None and os.path.exists(self.file_path):
            os.remove(self.file_path)
        mongo.db.videos.delete_one({'_id': ObjectId(self.id)})

    def try_update_from_imdb(self):
        movie_search = Video.getunicode('q={}'.format(self.title)).strip().replace(' ', '+')
        base_url = 'http://www.imdb.com'
        url = (base_url + '/find?' + movie_search + '&s=all').strip()
        print('url search: '+url)
        page = urllib.request.urlopen(url)
        soup = BeautifulSoup(page.read(), "html.parser")

        link = soup.find('table', {'class': 'findList'})
        link = link.tr.td.a['href']
        url = base_url + link
        print('url request: ' + url)
        page = urllib.request.urlopen(url)
        soup = BeautifulSoup(page.read(), 'html.parser')
        title_wrapper = soup.find('div', {'class': 'title_wrapper'})
        movie_title = Video.getunicode(title_wrapper.find('h1', {'itemprop': 'name'}).get_text())

        if title_wrapper.find('div', {'class': 'originalTitle'}) is None:
            original_title = movie_title
        else:
            original_title = Video.getunicode(title_wrapper.find('div', {'class': 'originalTitle'}).get_text())

        if title_wrapper.find('time', {'itemprop': 'duration'}) is None:
            duration = None
        else:
            duration = Video.getunicode(title_wrapper.find('time', {'itemprop': 'duration'}).get_text().strip())
        if title_wrapper.find('meta', {'itemprop': 'datePublished'}) is None:
            release_date = None
        else:
            release_date = Video.getunicode(title_wrapper.find('meta', {'itemprop': 'datePublished'})['content'])
        rate = soup.find('span', itemprop='ratingValue')
        if rate is None:
            rating = None
        else:
            rating = Video.getunicode(rate)

        actors = []
        actorstable = soup.find('table', {'class', 'cast_list'})
        try:

            if actorstable is not None:
                actors = list(set.union(set(
                    [Video.getunicode(a.find('span', {'class': 'itemprop', 'itemprop': 'name'}).get_text()) for a in
                     actorstable.findAll('tr', {'class': 'even'})]),
                    set([Video.getunicode(
                        a.find('span', {'class': 'itemprop', 'itemprop': 'name'}).get_text()) for a
                        in actorstable.findAll('tr', {'class': 'odd'})])))
        except:
            actors = []
        des = Video.getunicode(soup.find('meta', {'name': 'description'})['content'])
        originalimagelink = soup.find('meta', {'property': 'og:image'})['content']

        imdb_id = soup.find('meta', {'property': 'pageId'})['content']
        genre = []
        classgenre = soup.find('div', {'class': 'see-more inline canwrap', 'itemprop': 'genre'})
        if classgenre is not None:
            genrelist = classgenre.findAll('a', {'href': True})
            genre = [Video.getunicode(a) for a in classgenre.findAll('a', {'href': True})]
        else:
            genre = ['Unknown']
        data = {
            'title': movie_title,
            'release_date': release_date,
            'rating': rating,
            'duration': duration,
            'original_title': original_title,
            'genre': genre,
            'actors': actors,
            'summary': des,
            'image': originalimagelink,
            'imdb_id': imdb_id,
            'id': self.id,
            'image_path': self.image_path,
            'file_path': self.file_path,
            'torrent_status': self.torrent_status,
            'torrent_eta': self.torrent_eta,
            'torrent_progress': self.torrent_progress,
            'torrent_id': self.torrent_id
        }
        if self.torrent_status == 'seeding' and self.torrent_progress == 100 and self.torrent_id <= 0:
            self.torrent_status = 'converting'
            Thread(target=self.convert_video, args=(current_app._get_current_object(),)).start()
        mongo.db.videos.update({'title': self.title}, data)

        return json.dumps(data, sort_keys=True)

    def add_file_to_transmission(self, file):
        torr = tc.add_torrent(file, download_dir=current_app.config['FILMS_FOLDER'])
        self.torrent_id = torr.id
        torrent = tc.get_torrent(torr.id)
        self.torrent_status = torrent.status
        self.torrent_progress = torrent.progress
        try:
            self.torrent_eta = torrent.format_eta()
        except ValueError:
            self.torrent_eta = 'NA'
        files = tc.get_files()
        ids_to_not_download = [fileid for fileid in files[torr.id]
                               if os.path.splitext(files[torr.id][fileid]['name'])[1]
                               not in current_app.config['VIDEO_EXTENSIONS']]
        if len(ids_to_not_download) > 0:
            for id in ids_to_not_download:
                files[torr.id][id]['selected'] = 'False'
            tc.set_files(files)

        filenames = [a for a in torrent.files().values() if os.path.splitext(a['name'])[1]
                     in current_app.config['VIDEO_EXTENSIONS']]
        filename = None
        if len(filenames) > 0:
            filename = filenames[0]['name']
        if filename is not None:
            self.file_path = os.path.join(current_app.config['FILMS_FOLDER'], filename)


    def update_torrent_info(self):
        if self.torrent_id > 0:
            try:
                torr = tc.get_torrent(self.torrent_id)
                self.torrent_progress = torr.progress
                self.torrent_status = torr.status
                self.torrent_eta = torr.format_eta()
            except KeyError:
                self.torrent_id = -1
                self.torrent_status = 'error'

            except TransmissionError:
                print('Transmission error, restart  ')
            mongo.db.videos.update({'_id': ObjectId(self.id)},
                                   {'$set':
                                       {
                                           'torrent_id': self.torrent_id,
                                           'torrent_progress': self.torrent_progress,
                                           'torrent_status': self.torrent_status,
                                           'torrent_eta': self.torrent_eta
                                       }
                                   })

    def convert_video(self, app):
        if not os.path.exists(os.path.join(app.config['FILMS_FOLDER'], self.id + '.mp4')):
            if os.path.splitext(self.file_path)[1] == '.mp4':
                print('Moving file')
                shutil.move(self.file_path, os.path.join(app.config['FILMS_FOLDER'], self.id + '.mp4'))
            else:
                print('Start ffmpeg')
                subprocess.run(['ffmpeg', '-i', self.file_path, '-f', 'mp4', '-preset', 'fast', '-vcodec', 'libx264',
                                '-movflags', 'faststart',
                                os.path.join(app.config['FILMS_FOLDER'], self.id + '.mp4')])
                print('REMOVING FILE')
                os.remove(self.file_path)
            directories = [a for a in os.listdir(app.config['FILMS_FOLDER'] ) if os.path.commonprefix(
                [a, app.config['FILMS_FOLDER']]) != app.config['FILMS_FOLDER']]

            for directory in directories:
                shutil.rmtree(directory, ignore_errors=True)
            self.torrent_status = 'completed'
            self.file_path = os.path.join(app.config['FILMS_FOLDER'], self.id + '.mp4')

            mongo.db.videos.update({'_id': ObjectId(self.id)},
                                   {
                                       '$set':
                                           {
                                               'torrent_status': self.torrent_status,
                                               'file_path': self.file_path
                                           }
                                   })

    @staticmethod
    def video_download_procedure(app):
        with app.app_context():
            videos = mongo.db.videos.find_one({'torrent_status': 'converting'})
            if videos is not None:
                print('Converting old video already converting before')
                video = Video(videos)
                video.update_torrent_info()
                video.torrent_status = 'converting'
                mongo.db.videos.update({'_id': ObjectId(video.id)},
                                       {
                                           '$set':
                                               {
                                                   'torrent_status': video.torrent_status,
                                               }
                                       })
                try:
                    video.convert_video(app)
                except:
                    video.torrent_status = 'error'
                    mongo.db.videos.update({'_id': ObjectId(video.id)},
                                           {
                                               '$set':
                                                   {
                                                       'torrent_status': video.torrent_status,
                                                   }
                                           })
            while True:
                print('Start cycle!')
                time.sleep(5)
                videos = mongo.db.videos.find_one({'torrent_status': 'seeding', 'torrent_progress': 100})
                if videos is not None:
                    video = Video(videos)
                    video.update_torrent_info()
                    tc.remove_torrent(video.torrent_id)
                    video.torrent_id = -1
                    video.torrent_status = 'converting'
                    mongo.db.videos.update({'_id': ObjectId(video.id)},
                                           {
                                               '$set':
                                                   {
                                                       'torrent_status': video.torrent_status,
                                                       'torrent_id': video.torrent_id
                                                   }
                                           })
                    try:
                        video.convert_video(app)
                    except:
                        video.torrent_status = 'error'
                        mongo.db.videos.update({'_id': ObjectId(video.id)},
                                               {
                                                   '$set':
                                                       {
                                                           'torrent_status': video.torrent_status,
                                                       }
                                               })



    @staticmethod
    def update_video_torrents_info():
        videos = mongo.db.videos.find({'torrent_status': {'$ne': 'completed'}})
        for video in videos:
            Video(video).update_torrent_info()

    @staticmethod
    def add_video(title, file=''):
        if mongo.db.videos.find_one({'title': title}) is not None:
            return None
        vid_id = mongo.db.videos.insert({'title': title})
        video = Video.get_video(str(vid_id))
        if file != '':
            video.add_file_to_transmission(file)
        video.try_update_from_imdb()
        return video

    @staticmethod
    def get_list_videos(page_number, video_per_page):
        class Object(object):
            pass

        list_video = Object()
        list_video.has_prev = (page_number > 1)
        list_video.prev = page_number - 1
        list_video.next = page_number + 1
        cont = mongo.db.videos.count()
        list_video.has_next = (cont > video_per_page * page_number)
        skips = video_per_page * (page_number - 1)
        cursor = mongo.db.videos.find().skip(skips).limit(video_per_page)
        list_video.videos = [Video(video) for video in cursor]
        return list_video

    @staticmethod
    def get_video(id):
        video = mongo.db.videos.find_one({'_id': ObjectId(id)})
        if not video:
            return None
        return Video(video)

    @staticmethod
    def getunicode(soup):
        body = ''
        if isinstance(soup, str):
            soup = soup.replace('&#39;', "'")
            soup = soup.replace('&quot;', '"')
            soup = soup.replace('&nbsp;', ' ')
            soup = soup.replace('&nbsp;', ' ')
            soup = soup.replace(u'\xa0', '')
            body = body + soup
        else:
            if not soup.contents:
                return ''
            con_list = soup.contents
            for con in con_list:
                body = body + Video.getunicode(con)
        return body
