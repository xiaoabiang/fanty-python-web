# -*- coding: utf-8 -*-
from aiohttp import web
from www.models import User

__author__ = 'Administrator'


import inspect
from www.coroweb import get
import asyncio


# @get('/')
# @asyncio.coroutine
# def index(request):
#     return web.Response(body = b'<h1>Fanty</h1>')



@get('/')
def index(request):
    users = yield from User.findAll()
    return {
        '__template__': 'test.html',
        'users': users
    }