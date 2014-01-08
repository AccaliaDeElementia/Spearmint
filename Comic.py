#!/usr/bin/env python3
'''Spearmint Comic

    Comic plugin for Spearmint
'''
import os
from time import mktime
from zipfile import is_zipfile, ZipFile
import mimetypes
import cherrypy

import Utils

mimetypes.init()

class Comic(object):
    '''Spearmint Comic Plugin Main Class'''
    def __init__(self, path=None):
        '''Create Comic Library from `path`'''
        if not path:
            path = './'
        self.prefix = path

    @cherrypy.expose
    @Utils.jsonify
    def list(self, *args, **kwargs):
        '''Get Directory Listing for Comic Library'''
        Utils.allow_methods(kwargs=kwargs)
        path = '/'.join(args)
        if not os.path.isdir(self.prefix+path):
            raise cherrypy.HTTPError(404, 'Requested Directory Not Exists')
        retval = {
            'dirs': [],
            'files': []
        }
        base = self.prefix + path
        for item in Utils.sort_list(os.listdir(base), lambda x: x.lower()):
            safepath = path + '/' + item
            filename = base + '/' + item
            if os.path.isdir(filename):
                retval['dirs'].append(safepath)
            elif is_zipfile(filename):
                retval['files'].append(safepath)
        return retval

    @cherrypy.expose
    @Utils.jsonify
    def info(self, *args, **kwargs):
        '''Get Info About a Comic'''
        Utils.allow_methods(kwargs=kwargs)
        if len(args) < 1:
            raise cherrypy.HTTPError(400, 'No Comic Path Requested')
        path = '/'.join(args)
        filename = self.prefix + path
        if not is_zipfile(filename):
            raise cherrypy.HTTPError(404, 'Requested Comic Not Exists')
        comic = ZipFile(filename)
        name = Utils.filename_to_name(filename)
        comment = str(comic.comment, 'utf8')
        pages = Utils.sort_list([info for info in comic.infolist()
            if Utils.is_image(info.filename)], lambda x: x.filename.lower())
        modified = Utils.date_to_httpdate(os.path.getmtime(filename))
        etag = Utils.make_etag(path, modified)
        Utils.validate_conditional(etag, modified)
        return {
            'name': name,
            'comment': comment,
            'pagecount': len(pages),
            'pages': [
                {
                    'filename': page.filename,
                    'name': Utils.filename_to_name(page.filename),
                    'comment': str(page.comment, 'utf8'),
                    'size': page.file_size
                }
                for page in pages
            ]
        }

    @cherrypy.expose
    def image(self, *args, **kwargs):
        '''Get Image From Comic'''
        Utils.allow_methods(kwargs=kwargs)
        if len(args) < 2:
            raise cherrypy.HTTPError(400, 'No Comic Path Requested')
        path = '/'.join(args[:-1])
        index = -1
        try:
            index = int(args[-1])
        except ValueError:
            raise cherrypy.HTTPError(400, 'No Comic Page Requested')
        index -= 1
        base = self.prefix + path
        if not is_zipfile(base):
            raise cherrypy.HTTPError(404, 'Requested Comic Not Exists')
        comic = ZipFile(base)
        pages = Utils.sort_list([info for info in comic.infolist()
            if Utils.is_image(info.filename)], lambda x: x.filename.lower())
        if index < 0  or index >= len(pages):
            raise cherrypy.HTTPError(404, 'Requested Comic Page Not Exists')
        page = pages[index]
        modified = Utils.date_to_httpdate(mktime(page.date_time + (0, 0, 0)))
        etag = Utils.make_etag(path, index, modified)
        Utils.validate_conditional(etag, modified)
        types = mimetypes.guess_type(pages[index].filename)
        cherrypy.response.headers['Content-Type'] = types[0]
        return comic.read(pages[index])

if __name__ == '__main__':
    cherrypy.tree.mount(Comic(), '/', {
        '/': {
            'tools.encode.on': True,
            'tools.gzip.on': True
        }
    })
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.engine.start()
    cherrypy.engine.block()


