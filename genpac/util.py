# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os
import sys
import codecs
import re

from ._compat import PY2, string_types, binary_type, getcwd
from ._compat import unquote, urlparse
from .publicsuffixlist import PublicSuffixList


_PSL = None


class Error(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg.encode('utf-8') if PY2 else self.msg


class FatalError(Error):
    pass


class FatalIOError(FatalError):
    pass


def surmise_domain(rule):
    global _PSL

    def _clear_asterisk(rule):
        if rule.find('*') < 0:
            return rule
        rule = rule.strip('*')
        rule = rule.replace('/*.', '/')
        rule = re.sub(r'/([a-zA-Z0-9]+)\*\.', '/', rule)
        rule = re.sub(r'\*([a-zA-Z0-9_%]+)', '', rule)
        rule = re.sub(r'^([a-zA-Z0-9_%]+)\*', '', rule)
        return rule

    domain = ''

    rule = _clear_asterisk(rule)
    rule = rule.lstrip('.')

    if rule.find('%2F') >= 0:
        rule = unquote(rule)

    if rule.startswith('http:') or rule.startswith('https:'):
        r = urlparse(rule)
        domain = r.hostname
    elif rule.find('/') > 0:
        r = urlparse('http://' + rule)
        domain = r.hostname
    elif rule.find('.') > 0:
        domain = rule

    _PSL = _PSL or PublicSuffixList(accept_unknown=False, only_icann=True)
    return _PSL.suffix(domain)


def error(*args, **kwargs):
    print(*args, file=sys.stderr)
    if kwargs.get('exit', False):
        sys.exit(kwargs.get('exit_code') or 1)


def exit_error(*args, **kwargs):
    error(*args, exit=True, exit_code=kwargs.get('code') or 1)


def exit_success(*args):
    print(*args)
    sys.exit()


def abspath(path):
    return os.path.abspath(os.path.expanduser(path)) if path else getcwd()


def open_file(path, mode='r'):
    path = abspath(path)
    return codecs.open(path, mode, 'utf-8')


def read_file(path, fail_msg='读取文件{path}失败: {error}'):
    try:
        with open_file(path) as fp:
            return fp.read()
    except Exception as e:
        raise FatalIOError(fail_msg.format(**{'path': path, 'error': e}))


def write_file(path, content, fail_msg='写入文件{path}失败: {error}'):
    if isinstance(content, binary_type):
        content = content.decode('utf-8')
    try:
        with open_file(path, 'w') as fp:
            fp.write(content)
    except Exception as e:
        raise FatalError(fail_msg.format(**{'path': path, 'error': e}))


def get_resource_path(path):
    dir_path = os.path.dirname(__file__)
    dir_path = dir_path if dir_path else os.getcwd()
    return os.path.join(dir_path, path)


def open_resource(path, mode='r'):
    path = get_resource_path(path)
    return open_file(path, mode)


def get_resource_data(path):
    with open_resource(path) as fp:
        return fp.read()


def replace_all(text, replacements):
    def one_xlat(match):
        return replacements[match.group(0)]

    if not replacements:
        return text
    rx = re.compile('|'.join(map(re.escape, replacements)))
    return rx.sub(one_xlat, text)


def conv_bool(obj):
    if isinstance(obj, string_types):
        return True if obj.lower() == 'true' else False
    return bool(obj)


def conv_list(obj, sep=','):
    obj = obj or ''
    if isinstance(obj, list):
        obj = '\n'.join(obj)
    obj = obj.replace(sep, '\n')
    return [s.strip() for s in obj.splitlines() if s.strip()]


def conv_lower(obj):
    obj = obj or ''
    if isinstance(obj, string_types):
        return obj.lower()
    return obj


def conv_path(obj):
    if isinstance(obj, string_types):
        return abspath(obj)
    if isinstance(obj, list):
        return [abspath(p) for p in obj]
    return obj
