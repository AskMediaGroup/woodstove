# Copyright (c) 2013 Ask.com.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.
#
# Any express or implied warranties, including, without limitation, the implied
# warranties of merchantability and fitness for a particular purpose and any
# warranty of non-infringement are disclaimed.  The copyright owner and
# contributors shall not be liable for any direct, indirect, incidental,
# special, punitive, exemplary, or consequential damages (including, without
# limitation, procurement of substitute goods or services; loss of use, data or
# profits; or business interruption) however caused and under any theory of
# liability, whether in contract, strict liability, or tort (including
# negligence) or otherwise arising in any way out of the use of or inability to
# use the software, even if advised of the possibility of such damage.  The
# foregoing limitations of liability shall apply even if deemed to fail of
# their essential purpose.  The software may only be distributed under the
# terms of the License and this disclaimer.
''' CRUD App mixin '''


import json
import inspect
import bottle
from woodstove import exceptions, plugin
from woodstove.app import arguments
from woodstove.db import stormy
from woodstove.db import generic


def crud_hook(hook):
    '''
    Setup a CRUDApp method as a hook in the crud_hooks dict.

    @param table: Table to add to in.
    @param hook: Hook callback function.
    '''
    def setup(func):
        '''
        Decorator that adds a crud_hook attribute to the decorated function.

        @param func: Hook function to setup.
        '''
        func.crud_hook = hook
        return func

    return setup


class CRUD(object):
    '''

    @var crud_klass:
    @var crud_auth:
    @var crud_read_auth:
    @var crud_key_type:
    @var crud_key_name:
    @var crud_hooks:
    @var crud_find_limit:
    @var crud_fn:
    @var crud_argfmt:
    '''
    crud_klass = None
    crud_auth = True
    crud_read_auth = False
    crud_key_type = int
    crud_key_name = None
    crud_hooks = None
    crud_find_limit = None
    crud_fn = None
    crud_argfmt = None
    _crud_fn = None

    def __init__(self, *args, **kwargs):
        '''

        @param *args:
        @param **kwargs:
        '''
        super(CRUD, self).__init__()
        self._crud_argfmt = {
            'create': arguments.storm_to_spec(self.crud_klass),
            'update': arguments.storm_to_spec(self.crud_klass),
            'replace': arguments.storm_to_spec(self.crud_klass),
            'find': arguments.storm_to_spec(self.crud_klass),
        }

        if self.crud_argfmt:
            self._crud_argfmt.update(self.crud_argfmt)

        self._crud_fn = {
            'create': generic.create,
            'read': generic.get,
            'update': generic.update,
            'delete': generic.delete,
            'replace': generic.replace,
            'find': generic.find,
        }

        if self.crud_fn:
            self._crud_fn.update(self.crud_fn)

        for _, attr in inspect.getmembers(self):
            try:
                hook = attr.crud_hook
            except AttributeError:
                continue
            plugin.register_hook(self.__class__, hook, attr)

    def crud_auth_fn(self, key=None, data=None):
        '''

        @keyword key:
        @keyword data:
        '''
        self.auth()

    crud_read_auth_fn = crud_auth_fn

    def crud_encode(self, obj):
        '''

        @param obj:
        '''
        return stormy.storm_to_dict(obj)

    @post('/')
    def create(self, auth_callback=None):
        ''' '''
        data = self.validate(self._crud_argfmt['create'], func='create')
        if self.crud_auth:
            if not auth_callback:
                auth_callback = self.crud_auth_fn
            auth_callback(data=data)
        self.set_status(201)
        return self.response(self.crud_encode(self._crud_fn['create'](
            self.crud_klass, data)))

    @get('/:key')
    def read(self, key, auth_callback=None):
        ''' '''
        try:
            key = self.crud_key_type(key)
        except ValueError:
            raise exceptions.RequestException('Invalid key')
        if self.crud_read_auth:
            if not auth_callback:
                auth_callback = self.crud_read_auth_fn
            auth_callback(key)
        return self.response(self.crud_encode(self._crud_fn['read'](
            self.crud_klass, key)))

    @post('/:key')
    def update(self, key, auth_callback=None):
        ''' '''
        data = self.validate(self._crud_argfmt['update'], func='update')
        try:
            key = self.crud_key_type(key)
        except ValueError:
            raise exceptions.RequestException('Invalid key')
        if self.crud_auth:
            if not auth_callback:
                auth_callback = self.crud_auth_fn
            auth_callback(key, data)
        return self.response(self.crud_encode(self._crud_fn['update'](
            self.crud_klass, key, data)))

    @put('/:key')
    def replace(self, key, auth_callback=None):
        ''' Replace existing record or create new one with specified key '''
        try:
            key = self.crud_key_type(key)
        except ValueError:
            raise exceptions.RequestException('Invalid key')
        body = self.body()
        body[self.crud_key_name] = key
        data = self.validate(self._crud_argfmt['replace'], body,
                             func='replace')
        if self.crud_auth:
            if not auth_callback:
                auth_callback = self.crud_auth_fn
            auth_callback(key)
        if not self.crud_key_name:
            raise
        try:
            ret = self._crud_fn['replace'](self.crud_klass, self.crud_key_name,
                                           key, data)
        except exceptions.NotFoundException:
            self.set_status(201)
            data[self.crud_key_name] = key
            ret = self._crud_fn['create'](self.crud_klass, data)
        return self.response(self.crud_encode(ret))

    @delete('/:key')
    def delete(self, key, auth_callback=None):
        ''' '''
        try:
            key = self.crud_key_type(key)
        except ValueError:
            raise exceptions.RequestException('Invalid key')
        if self.crud_auth:
            if not auth_callback:
                auth_callback = self.crud_auth_fn
            auth_callback(key)
        return self.response(self.crud_encode(self._crud_fn['delete'](
            self.crud_klass, key)))

    @get('/')
    def find(self, auth_callback=None):
        ''' '''
        if self.crud_read_auth:
            if not auth_callback:
                auth_callback = self.crud_read_auth_fn

            auth_callback()

        try:
            limit = bottle.request.query.get('limit', self.crud_find_limit)
            args = dict({
                'where': json.loads(bottle.request.query.get('where', '{}')),
                'offset': int(bottle.request.query.get('offset', 0)),
                'limit': limit if limit is None else int(limit),
                'sort': bottle.request.query.get('sort', None),
            })
        except ValueError:
            raise exceptions.ArgumentException

        self.validate(self._crud_argfmt['find'], args['where'], False)
        ret = list(self._crud_fn['find'](self.crud_klass, **args))
        ret[0] = [self.crud_encode(x) for x in ret[0]]
        return self.response(ret[0], total=ret[1])
