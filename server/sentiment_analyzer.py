#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division
import json, re

import flask as flask
from flask import redirect, request
from flask.ext.cors import cross_origin

# the circular dependency is ok in this case
from server import app

# import ruleBased

lines = [ (re.split(',', line)) for line in open('merge.csv').read().splitlines() ]
lexicon = { word: float(score) for word, score in lines }


# The routes for the sentiment analyzer
@app.route('/sentiment/<lang>', methods=['GET'])
@cross_origin(methods=['GET'], send_wildcard=True, always_send=True)
def convert_morphology(lang):
    if lang == 'en':
        # get params from the request
        tweet = request.args['tweet']
        return flask.jsonify({ tweet: tweet })
    else:
        return flask.jsonify({ "error": "I don't know the language: " + lang })