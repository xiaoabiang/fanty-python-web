# -*- coding: utf-8 -*-
import hashlib
from aiohttp import web
import time
import re
from www.apis import APIValueError, APIError
from www.models import User, Blog, next_id
import json

__author__ = 'Administrator'


import inspect
from www.coroweb import get, post
import asyncio


# @get('/')
# @asyncio.coroutine
# def index(request):
#     return web.Response(body = b'<h1>Fanty</h1>')



# @get('/')
# def index(request):
#     users = yield from User.findAll()
#     return {
#         '__template__': 'test.html',
#         'users': users
#     }


@get('/')
def index(request):
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }


@get("/api/users")
def api_get_users(request):
    users = yield from User.findAll()
    for u in users:
        u.passwd = '******'
    return dict(users=users)


_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

@post("/api/users")
def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = yield from User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    uid = next_id()
    sha1_password = '%s:%s' % (uid, passwd)
    user = User(id=uid, name=name.strip(), email=email,passwd=hashlib.sha1(sha1_password.encode('utf-8').hexdigest(),
                image=''))
    yield from user.save()
    r = web.Response()
    r.set_cookie(COOKIE_NAME,user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user,ensure_ascii=False).enconde('utf-8')
    return r

