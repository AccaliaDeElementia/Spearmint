#!/usr/bin/env python3
'''Spearmint Gallery

    Gallery Plugin for Spearmint
'''
import os
import mimetypes
import cherrypy
from urllib import parse as urllib
import Utils

mimetypes.init()

class Gallery(object):
    '''Spearmint Gallery Plugin Main Class'''
    def __init__(self, path=None):
        '''Create Gallery from `path`'''
        if not path:
            path = '/storage/accalia/image/'
        self.prefix = path

    @cherrypy.expose
    @Utils.jsonify
    def listdir(self, *args, **kwargs):
        '''Get Directory Listing for Gallery'''
        Utils.allow_methods(kwargs=kwargs)
        path = Utils.urlpatherize(args)
        if not os.path.isdir(self.prefix + path):
            raise cherrypy.HTTPError(404, 'Requested Directory Not Exists')
        retval = {
            'dirs': [],
            'files': []
        }
        base = self.prefix + path
        if path:
            path = '/' + path
        for item in Utils.sort_list(os.listdir(base), lambda x: x.lower()):
            safepath = path + '/' + item
            filename = base + '/' + item
            if os.path.isdir(filename):
                retval['dirs'].append(safepath)
            else:
                types = mimetypes.guess_type(filename)
                if types[0] and types[0].startswith('image/'):
                    retval['files'].append(safepath)
        return retval

    @cherrypy.expose
    def image(self, * args, **kwargs):
        '''Get Image From The Gallery'''
        Utils.allow_methods(kwargs=kwargs)
        path = Utils.urlpatherize(args)
        filename = self.prefix + path
        if not os.path.isfile(filename):
            raise cherrypy.HTTPError(404, 'File Not Found')
        try:
            types = mimetypes.guess_type(filename)
            cherrypy.response.headers['Content-Type'] = types[0]
            modified = Utils.date_to_httpdate(os.path.getmtime(filename))
            etag = Utils.make_etag(filename, modified)
            Utils.validate_conditional(etag, modified)
            with open(filename, 'rb') as file:
                return file.read()
        except IOError:
            raise cherrypy.HTTPError(403, 'Permission denied')


if __name__ == '__main__':
    cherrypy.tree.mount(Gallery(), '/')
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.engine.start()
    cherrypy.engine.block()
