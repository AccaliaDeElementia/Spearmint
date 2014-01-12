'''Utility functions for Spearmint.'''
import re
import cherrypy
import mimetypes
from time import time
from wsgiref.handlers import format_date_time
from zlib import crc32
from json import dumps

mimetypes.init()

def urlpatherize(parts):
    '''Join the path and correct cherrypy's faulty latin1 encoding'''
    path = '/'.join(parts)
    path = path.encode('latin1').decode('utf8')
    return path

def jsonify(func):
    '''Decorator that JSON stringify method results'''
    def __inner(*args, **kwargs):
        '''Do the jsonification!'''
        response = cherrypy.serving.response
        response.headers['Content-Type'] = 'application/json'
        return bytes(dumps(func(*args, **kwargs), indent=2) + '\n', 'utf8')
    __inner.__name__ = func.__name__
    __inner.__doc__ = func.__doc__
    __inner.__module__ = func.__module__
    return __inner

def filename_to_name(filename):
    '''Turn a filename into a more human friendly name.

    This is non-reversible as path and extension data is discarded.'''
    name = filename.rsplit('/', 1)[-1].rsplit('.', 1)[0]
    return name.replace('_', ' ')

def is_image(item):
    '''Return true if is image mimetype'''
    types = mimetypes.guess_type(item)
    return bool(types[0] and types[0].startswith('image/'))

def make_etag(*args):
    '''Turn argument list into ETag'''
    encode = lambda x: '%X' % crc32(bytes(str(x), 'utf8'))
    return ':'.join(encode(arg) for arg in args)

def sort_list(collection, getkey=lambda x: x):
    '''Return a new, sorted list from collection'''
    tokenize = re.compile(r'(\d+)|(\D+)').findall
    def key(item):
        '''Turn item into a key tuple'''
        return tuple(num.rjust(20, '0') if num else alpha for num, alpha
            in tokenize(getkey(item)))
    return sorted(collection, key=key)

def allow_methods(methods=('GET', 'HEAD'), allow_form=True, kwargs=None):
    '''Allow only centrain HTTP Methods'''
    request = cherrypy.serving.request
    response = cherrypy.serving.response
    response.headers['Allow'] = ', '.join(methods)
    if request.method not in methods:
        raise cherrypy.HTTPError(405)
    if not allow_form and kwargs:
        raise cherrypy.HTTPError(400, 'Form input not allowed for endpoint')

def date_to_httpdate(date):
    '''Turn a datetime into a httpdate string'''
    return format_date_time(date)

def validate_conditional(etag, modified, cache_time=14):
    '''Validate conditional headers.'''
    def not_modified():
        '''Raise the correct not modified event'''
        if request.method in ('GET', 'HEAD'):
            raise cherrypy.HTTPRedirect([], 304)
        else:
            raise cherrypy.HTTPError(412)
    request = cherrypy.serving.request
    response = cherrypy.serving.response
    expires = time() + cache_time * 24 * 60 * 60
    etag = etag.strip()
    modified = modified.strip()
    #Last-Modified
    since = request.headers.get('If-Unmodified-Since')
    if since and modified != since:
        raise cherrypy.HTTPError(412)
    since = request.headers.get('If-Modified-Since')
    if since and modified == since:
        not_modified()

    #ETag
    conditions = request.headers.elements('If-Match') or []
    conditions = [str(x) for x in conditions]
    if conditions and not (conditions == ['*'] or etag in conditions):
        raise cherrypy.HTTPError(412)
    conditions = request.headers.elements('If-None-Match') or []
    conditions = [str(x) for x in conditions]
    if conditions == ['*'] or etag in conditions:
        not_modified()

    #Set Headers
    response.headers['Last-Modified'] = modified
    response.headers['ETag'] = etag
    response.headers['Expires'] = date_to_httpdate(expires)
