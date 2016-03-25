# -*- coding: utf-8 -*-
from aiohttp import web

__author__ = 'Administrator'


import inspect
from www.coroweb import get
import asyncio


@get('/')
@asyncio.coroutine
def index(request):
    return web.Response(body = b'<h1>Fanty</h1>')
