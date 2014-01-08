#!/usr/bin/env python3
import cherrypy

from Gallery import Gallery
from Comic import Comic

def application(environ, start_response):
    cherrypy.tree.mount(Gallery(), '/gallery/', None)
    cherrypy.tree.mount(Comic(), '/comic/', None)
    return cherrypy.tree(environ, start_response)
