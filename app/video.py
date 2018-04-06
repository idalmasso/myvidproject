from app import mongo
from bson.objectid import ObjectId
import os
from bs4 import BeautifulSoup
import urllib.request
import json
import transmissionrpc


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
            self.file_name = os.path.basename(self.file_path)


    def try_update_from_imdb(self):
        movie_search = Video.getunicode('q={}'.format(self.title)).strip().replace(' ', '+')
        base_url = 'http://www.imdb.com'
        url = (base_url + '/find?' + movie_search + '&s=all').strip()
        print(url)
        page = urllib.request.urlopen(url)
        soup = BeautifulSoup(page.read(), "html.parser")

        link = soup.find('table', {'class': 'findList'})
        link = link.tr.td.a['href']
        url = base_url + link

        page = urllib.request.urlopen(url)
        soup = BeautifulSoup(page.read(), 'html.parser')
        titlewrapper = soup.find('div', {'class': 'title_wrapper'})
        movie_title = Video.getunicode(titlewrapper.find('h1', {'itemprop': 'name'}).get_text())

        if titlewrapper.find('div', {'class': 'originalTitle'}) is None:
            original_title = movie_title
        else:
            original_title = Video.getunicode(titlewrapper.find('div', {'class': 'originalTitle'}).get_text())

        if titlewrapper.find('time', {'itemprop': 'duration'}) is None:
            duration = None
        else:
            duration = Video.getunicode(titlewrapper.find('time', {'itemprop': 'duration'}).get_text().strip())
        if titlewrapper.find('meta', {'itemprop': 'datePublished'}) is None:
            release_date=None
        else:
            release_date = Video.getunicode(titlewrapper.find('meta', {'itemprop': 'datePublished'})['content'])
        rate = soup.find('span', itemprop='ratingValue')
        if rate is None:
            rating = None
        else:
            rating = Video.getunicode(rate)

        actors = []
        actorstable = soup.find('table', {'class', 'cast_list'})

        if actorstable is not None:
            actors = list(set.union(set(
                [Video.getunicode(a.find('span', {'class': 'itemprop', 'itemprop': 'name'}).get_text()) for a in
                 actorstable.findAll('tr', {'class': 'even'})]),
                                    set([Video.getunicode(
                                        a.find('span', {'class': 'itemprop', 'itemprop': 'name'}).get_text()) for a
                                         in actorstable.findAll('tr', {'class': 'odd'})])))

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
            'file_path': self.file_path
        }
        mongo.db.videos.update({'title': self.title}, data)
        return json.dumps(data, sort_keys=True)

    def add_file_to_transmission(file):
        tc = transmissionrpc.Client('localhost', port=9091)
        tc.add_torrent(file)
		
	@staticmethod
    def add_video( title, file=''):
        if mongo.db.videos.find_one({'title':title}) is not None:
            return None
        vid_id = mongo.db.videos.insert({'title':title}).inserted_id
        video = Video.get_video(str(vid_id))
        video.try_update_from_imdb()
        if file != '':
            add_file_to_transmission(file)
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
        skips = video_per_page*(page_number-1)
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
