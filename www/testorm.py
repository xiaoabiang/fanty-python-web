# -*- coding: utf-8 -*-
__author__ = 'Administrator'

import orm
import models
import asyncio
import sys



def test(loop):
    yield from orm.create_pool(loop=loop, user='xiaoabiang', password='xiaoabiang', db='awesome')
    users = yield from models.User.findAll()
    test1 = dict()

    for user in users:
        test1[id] = user.id
        user2 = yield from models.User.find(test1)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop))
    loop.close()

if loop.is_closed():
    sys.exit(0)

