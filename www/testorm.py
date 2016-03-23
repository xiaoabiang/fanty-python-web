# -*- coding: utf-8 -*-
__author__ = 'Administrator'

import orm
import models
import asyncio
import sys
# class User(Model):
#     __table__ = 'users'
#     id = StringField(column_pk=True, column_default=next_id, column_type='varchar(50)')
#     email = StringField(column_type='varchar(50)')
#     passwd = StringField(column_type='varchar(50)')
#     admin = BooleanField()
#     name = StringField(column_type='varchar(50)')
#     image = StringField(column_type='varchar(500)')
#     created_at = FloatField(column_default=time.time)


# def test(loop):
#     yield from orm.create_pool(loop=loop, user='xiaoabiang', password='xiaoabiang', db='awesome')
#     users = yield from models.User.findAll()
#     for user in users:
#         user2 = yield from models.User.find(id = user.id)
#         for test in user2:
#             print(test)

def test(loop):
    yield from orm.create_pool(loop=loop, user='xiaoabiang', password='xiaoabiang', db='awesome')
    users = yield from models.User.findAll()
    for user in users:
        if user.email == 'test@163.com':
            user.email = 'test1@163.com'
            yield from user.update()
    # user = models.User(name = 'fanty',passwd = 'xiaoabiang',email = 'iiiaaa@163.com')
    # bool = yield from user.save()
    # if bool:
    #     print('保存成功！')
    # else:
    #     print('再接再厉！')



if __name__=='__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop))
    loop.close()

if loop.is_closed():
    sys.exit(0)

