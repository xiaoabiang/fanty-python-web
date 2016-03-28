# -*- coding: utf-8 -*-

__author__ = 'Administrator'


import logging
import asyncio
from logging import log
import aiomysql


def log(sql, args=()):
    logging.info('SQL: %s' % sql)

@asyncio.coroutine
def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )


@asyncio.coroutine
def select(sql, args, size=None):
    log(sql, args)
    global __pool
    with (yield from __pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        yield from cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        cur.close()
        conn.close()
        logging.info('rows returned: %s' % len(rs))
        return rs

@asyncio.coroutine
def execute(sql, args, autocommit=True):
    log(sql, args)
    global __pool
    with (yield from __pool) as conn:
        if not autocommit:
            yield from conn.begin()
        try:
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replace('?', '%s'), args or ())
            affected = cur.rowcount
            yield from cur.close()
            if not autocommit:
                yield from conn.commit()
        except BaseException as e:
            if not autocommit:
                yield from conn.rollback
            raise
        conn.close()
        return affected



#定义字段类型
class Field(object):
    #字段名，字段类型，是否主键，默认值
    def __init__(self, column_name, column_type, column_pk, column_default):
        self.column_name = column_name
        self.column_type = column_type
        self.column_pk = column_pk
        self.column_default = column_default

    #返回字段类型和字段名
    def __str__(self):
        return '<%s - %s：%s>' % (self.__class__.__name__, self.name, self.column_type)

#整数类型
class IntegerField(Field):
    def __init__(self, column_name=None, column_type='int', column_pk=False, column_default=0):
        super().__init__(column_name, column_type, column_pk, column_default)

#字符串类型
class StringField(Field):
    def __init__(self,column_name = None,column_type = 'varchar(100)', column_pk = False,column_default = ''):
        super().__init__(column_name, column_type, column_pk, column_default)


class FloatField(Field):
    def __init__(self,column_name = None,column_type = 'real', column_pk = False,column_default = 0):
        super().__init__(column_name, column_type, column_pk, column_default)


class BooleanField(Field):
    def __init__(self,column_name = None,column_type = 'boolean', column_pk = False,column_default = False):
        super().__init__(column_name,column_type, column_pk, column_default)

class TextField(Field):
    def __init__(self,column_name = None, column_type = 'text', column_pk = False,column_default = None):
        super().__init__(column_name, column_type, column_pk, column_default)


#定义数据属性表的元类
class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if(name == 'Model'):
            return type.__new__(cls, name, bases, attrs)

        tableName = attrs.get('__table__', None) or name
        mappings = {}
        fields = []
        primaryKey = []
        for k, v in attrs.items():
            if isinstance(v, Field):
                mappings[k] = v
                if v.column_pk:
                    primaryKey.append(k)
                fields.append(k)
        if len(primaryKey) == 0:
            raise RuntimeError('Primary kay not found.')
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        for k in mappings.keys():
            attrs.pop(k)
        #属性和列的映射关系
        attrs['__mappings__'] = mappings
        attrs['__fields__'] = fields
        attrs['__primaryKey__'] = primaryKey
        attrs['__tablename__'] = tableName
        attrs['__select__'] = 'select %s from %s'% (','.join(escaped_fields), tableName)
        attrs['__update__'] = 'update %s set %s where %s'%(tableName, ','.join(create_args_strings(fields)), 'and'.join(create_args_strings(primaryKey)))
        attrs['__delete__'] = 'delete from %s where %s' % (tableName, 'and'.join(create_args_strings(primaryKey)))
        attrs['__insert__'] = 'insert into %s (%s) values (%s)' % (tableName, ', '.join(escaped_fields), create_args_string(len(escaped_fields)))
        return type.__new__(cls, name, bases, attrs)

def create_args_strings(lists):
    return list(map(lambda item:'`%s` = ?' % item, lists))


def create_args_string(number):
    L=[]
    for n in range(number):
        L.append('?')
    return ','.join(L)


class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self,key):
        return getattr(self,key,None)


    def getValueOrDefault(self, key):
        value = getattr(self,key,None)
        if value is None:
            field = self.__mappings__[key]
            if field.column_default is not None:
                value = field.column_default() if callable(field.column_default) else field.column_default
                logging.debug('using default value for %s:%s' % (key , str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    @asyncio.coroutine
    def findAll(cls, where=None, args=None, **kw):
        'find objects by where clause.'
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = yield from select(' '.join(sql), args)
        return [cls(**r) for r in rs]



    @classmethod
    @asyncio.coroutine
    def find(cls, **pk):
        sqlStr = cls.__select__ + ' where '
        for k,v in pk.items():
            sqlStr += " `%s` = '%s' " % (k,v)
        rs = yield from select(sqlStr,pk)
        if len(rs) == 0:
            return None
        return [cls(**r) for r in rs]


    @asyncio.coroutine
    def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        # sqlstr = self.__insert__.replace('?', '%s')
        row = yield from execute(self.__insert__, args)
        if row != 1:
            return False
        return True

    @asyncio.coroutine
    def update(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        for pk in self.__primaryKey__:
            args.append(self.getValue(pk))
        row = yield from execute(self.__update__, args)
        if row != 1:
            return False
        return True

    @asyncio.coroutine
    def delete(self):
        args = list(map(self.getValueOrDefault, self.__primaryKey__))
        row = yield from execute(self.__delete__, args)
        if row != 1:
            return False
        return True
