# -*- coding: utf-8 -*-
from www.coroweb import add_routes

__author__ = 'Administrator'

import logging
import  asyncio,os,json,time
from datetime import datetime
from aiohttp import web
import www.orm
import www.config
import www.handlers

# 一个记录URL日志的logger
@asyncio.coroutine
def logger_factory(app,handler):
    @asyncio.coroutine
    def logger(request):
        # 记录日志
        logging.info('Request:%s %s' % (request.method,request.path))
        # 继续处理请求
        return(yield from handler(request))
    return logger


# 数据处理
@asyncio.coroutine
def data_factory(app,handler):
    @asyncio.coroutine
    def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = yield from request.json()
                logging.info('request json:%s' % str(request.__data__))
                # application/x-www-form-urlencoded ： 窗体数据被编码为名称/值对。这是标准的编码格式。
                # multipart/form-data ： 窗体数据被编码为一条消息，页上的每个控件对应消息中的一个部分。
                # text/plain ： 窗体数据以纯文本形式进行编码，其中不含任何控件或格式字符。
            elif request.content_type.startswith('application/x-www-from-unlencoded'):
                request.__data__ = yield from request.post()
                logging.info('request from:%s' % str(request.__data__))
        return (yield from handler(request))
    return parse_data


#返回的处理
@asyncio.coroutine
def response_factory(app,handler):
    @asyncio.coroutine
    def response(request):
        logging.info('Response handler...')
        r = yield from handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body= r.encode('utf-8'))
            resp.content_type = 'txt/html;charset = utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r,ensure_ascii=False,default=lambda o:o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r>=100 and r<600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t>= 100 and t < 600:
                return web.Response(t, str(m))
        #default
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset = utf-8'
        return resp
    return response


def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%分钟前' % (delta//60)
    if delta < 86400:
        return u'%小时前' % (delta//3600)
    if delta < 604800:
        return u'%天前' % (delta//86400)
    dt = datetime.fromtimestamp(t)
    return u'%年%月%日' % (dt.year, dt.month, dt.day)


@asyncio.coroutine
def init(loop):
    yield from www.orm.create_pool(loop=loop, host=configs['db']['host'], port=configs['db']['port'],
                               user=configs['db']['username'], password=configs['db']['password'], db=configs['db']['database'])
    app = web.Application(loop=loop, middlewares=[logger_factory, response_factory])
    add_routes(app, 'handlers')
    # app.router.add_route('GET', '/', www.handlers.index)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000....')
    return srv


if __name__ == '__main__':
    global configs
    configs = www.config.configs
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    loop.run_forever()