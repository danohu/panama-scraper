#!/usr/bin/python

import web

urls = ("/?.*", "hello")

class hello: 
    def GET(self):
        #web.header('Content-Type', 'text/html') 
        html = '<html><h2>Temporarily Unavailable</h2> '
        html += '</html>'
        return html

application = web.application(urls, globals()).wsgifunc()
#web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
#if __name__ == "__main__":
#    app.run()
