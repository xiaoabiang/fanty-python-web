# -*- coding: utf-8 -*-
__author__ = 'Administrator'


import conf.conf_default, conf.conf_over


def merge(dictold, dictadd):
    for k, v in dictadd.items():
        if isinstance(v, dict):
            merge(dictold[k], dictadd[k])
        else:
            dictold[k] = dictadd[k]
    return dictold

configs = merge(conf.conf_default.configs, conf.conf_over.configs)

if __name__ == '__main__':
    print(configs)

