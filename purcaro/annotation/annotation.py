#!/usr/bin/env python

import os, sys, json, cherrypy, jinja2, argparse
import numpy as np
import uuid
import StringIO

from db import AnnotationDB
from session import Sessions
from ucsc_search import UcscSearch

sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from utils import Utils
from trackhub import TrackHub
from web_epigenomes import WebEpigenomesLoader

class Templates:
    def __init__(self, viewDir):
        self.views = jinja2.Environment(loader=jinja2.FileSystemLoader(viewDir))

    def __call__(self, t, **kwargs):
        if "title" not in kwargs:
            kwargs["title"] = ""
        if "meta" not in kwargs:
            kwargs["meta"] = []
        return self.views.get_template(t+".html").render(kwargs)

class AnnotationSearchUcsc(object):
    def __init__(self, dbs, args):
        self.args = args

        self.db = AnnotationDB(dbs)
        self.sessions = Sessions(dbs)

        viewDir = os.path.join(os.path.dirname(__file__), "views")
        self.templates = Templates(viewDir)

        self.epigenomes = WebEpigenomesLoader()

        self.host = "http://bib7.umassmed.edu/ws/"
        if self.args.local:
            fnp = os.path.expanduser("~/.ws_host.txt")
            if os.path.exists(fnp):
                self.host = open(fnp).read().strip()

    @cherrypy.expose
    def default(self, *args, **params):
        return self.templates("index",
                              epigenomes = self.epigenomes)

    def makeUid(self):
        return str(uuid.uuid4())

    @cherrypy.expose
    def ucsc(self, *args, **params):
        uid = self.sessions.get(cherrypy.session.id)
        if not uid:
            uid = self.makeUid()
            cherrypy.session["uid"] = uid
            self.sessions.insertOrUpdate(cherrypy.session.id, uid)

        us = UcscSearch(self.epigenomes, self.db, self.host, params, uid)
        us.parse()
        url = us.configureUcscHubLink()

        if self.args.debug:
            return self.templates("ucsc",
                                  us = us,
                                  url = url)
        raise cherrypy.HTTPRedirect(url, 303)

    @cherrypy.expose
    def trackhubCustom(self, *args, **params):
        cherrypy.response.headers['Content-Type'] = 'text/plain'

        uid = args[0]
        row = self.db.get(uid)
        if not row:
            raise Exception("uuid not found")

        th = TrackHub(self.args, self.epigenomes, row)
        return th.Custom()

    @cherrypy.expose
    def trackhub(self, *args, **params):
        cherrypy.response.headers['Content-Type'] = 'text/plain'

        uid = args[0]
        row = self.db.get(uid)
        if not row:
            raise Exception("uuid not found")

        th = TrackHub(self.args, self.epigenomes, row)

        path = args[1:]
        return th.ParsePath(path)
