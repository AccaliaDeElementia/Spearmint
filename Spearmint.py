#!/usr/bin/env python3
'''Spearmint Server.

   Spearmint is an HTML5 based comic book archive (CBZ) reader. This is the 
   server side.
'''
from flask import Flask, send_file
from zipfile import ZipFile
from io import BytesIO
import mimetypes
import re


mimetypes.init()
STRTOK = re.compile(r'(\d+)|(\D+)').findall
APP = Flask(__name__)

def sort_collection(collection, getkey = lambda x: x):
    '''Return a "naturalish" sorted version of collection
    '''
    def getsortkey(item):
        '''Tokenize the item name for "naturalish" sort

        Takes all numeric sub sequences and pads them out with leading 0's.
        Not the most elegant solutionm but should work 98+% of the time.
        '''
        return tuple(num.rjust(20, '0') if num else alpha for num, alpha in
            STRTOK(getkey(item)))
    return sorted(collection, key=getsortkey)

class SpearmintComic (object):
    '''SpearmintComic is the Comic Book Object. We store it in session to 
       avoid having to do expensive operations on every request.
    '''
    def __init__(self, filename):
        self.__comic = ZipFile(filename)
        self.name = filename
        self.__position = 0

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, type_, value, traceback):
        self.close()

    def close(self):
        '''Close the Comic book in preparation to putting it away
        '''
        #pylint: disable=W0703
        if self.__comic:
            try:
                self.__comic.close()
            except Exception:
                pass # We're throwing the object away soon anyway.
            self.__comic = None

    def __pages(self):
        '''Return a sorted list of ZipInfo objects that are the comic pages in
           order
        '''
        def is_image(item):
            '''Used for sorting out non images from archive
            '''
            types = mimetypes.guess_type(item)
            return types[0] and types[0].startswith('image/')
        infos = self.__comic.infolist()
        return sort_collection([info for info in infos if 
            is_image(info.filename)], lambda x: x.filename.lower())

    def get_page_count(self):
        '''return number of pages in comic'''
        return len(self.__pages())

    def get_pages(self):
        '''Return an iterator that lists comic pages in order
        '''
        for page in self.__pages():
            yield page.filename

    def get_page(self, index):
        '''Get the page at /index/.
        '''
        pages = self.__pages()
        if index < 0 or index >= len(pages):
            raise IndexError('index out of range')
        return pages[index], self.__comic.read(pages[index])

@APP.route('/')
def test():
    '''This is just testing
    '''
    #pylint: disable=W0703
    try:
        comic = SpearmintComic('test.cbz')
        info, page = comic.get_page(0)
        return send_file(BytesIO(page),
            attachment_filename = info.filename,
            add_etags = True,
            conditional = True,
            cache_timeout = 60 * 60 * 20 * 6)
    except Exception as ex:
        print(repr(ex))

if __name__ == '__main__':
    APP.run()
        
