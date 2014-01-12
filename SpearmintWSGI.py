#!/usr/bin/env python3
import cherrypy

from Gallery import Gallery
from Comic import Comic

def application(environ, start_response):
    cherrypy.tree.mount(Gallery('/storage/accalia/images/'), '/gallery/', None)
    cherrypy.tree.mount(Comic(), '/comic/', None)
    cherrypy.config["tools.encode.on"] = True
    cherrypy.config["tools.encode.encoding"] = "utf-8"
    cherrypy.config["tools.decode.on"] = True
    cherrypy.config["tools.decode.encoding"] = "utf-8"
    return cherrypy.tree(environ, start_response)
