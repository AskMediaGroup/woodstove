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
''' Generic database utilities '''


from storm.expr import Desc
from storm.exceptions import NotOneError
from woodstove.db import stormy
from woodstove import exceptions, plugin


def find(stype, where=None, offset=0, limit=None, sort=None,
                 distinct=False):
    '''
    @param stype:
    @keyword where:
    @keyword offset:
    @keyword limit:
    @keyword sort:
    @keyword distinct:
    '''
    hook_storage = dict()
    sort_desc = False
    query = stormy.Query(stype)
    query.offset = offset
    query.limit = limit
    plugin.call_hooks(stype, 'find.using', query, storage=hook_storage)

    if sort:
        if sort.startswith('-'):
            sort = sort[1:]
            query.desc = True

        try:
            query.order = getattr(stype, sort)

            if sort_desc:
                query.order = Desc(query.order)
        except AttributeError:
            pass

    if where:
        query.where = stormy.gen_expr(stype, where)

    plugin.call_hooks(stype, 'find.where', where, query, storage=hook_storage)
    plugin.call_hooks(stype, 'find.sort', sort, query, storage=hook_storage)
    return query.execute()


def find_one(stype, expr=None, **kwargs):
    '''
    @param stype:
    @keyword expr:
    @keyword **kwargs:
    @return:
    @raise NotFoundException:
    '''
    hook_storage = dict()
    store = stormy.Stormy()
    plugin.call_hooks(stype, 'find_one.prefind', expr, kwargs,
                      storage=hook_storage)

    try:
        obj = store.find(stype, expr=expr, **kwargs).one()
    except NotOneError:
        raise

    if not obj:
        plugin.call_hooks(stype, 'find_one.notfound', expr, kwargs,
                          storage=hook_storage)
        raise exceptions.NotFoundException

    plugin.call_hooks(stype, 'find_one.postfind', expr, kwargs, obj,
                      storage=hook_storage)
    return obj


def create(stype, data):
    '''
    Create an object of stype and add it to db

    @param stype:
    @param data:
    @return:
    '''
    hook_storage = dict()
    store = stormy.Stormy()
    new = stype()
    plugin.call_hooks(stype, 'create.preset', new, data, storage=hook_storage)
    stormy.dict_set(new, data)
    plugin.call_hooks(stype, 'create.postset', new, storage=hook_storage)
    store.add(new)
    plugin.call_hooks(stype, 'create.precommit', new, storage=hook_storage)
    store.commit()
    plugin.call_hooks(stype, 'create.postcommit', new, storage=hook_storage)
    return new


def get(stype, key):
    '''
    Get an object from db
    
    @param stype:
    @param key:
    @raises NotfoundException: If requested object does not exist.
    @return: Instance of L{stype} with key L{key}.
    '''
    hook_storage = dict()
    store = stormy.Stormy()
    plugin.call_hooks(stype, 'get.preget', key, storage=hook_storage)
    obj = store.get(stype, key)

    if not obj:
        plugin.call_hooks(stype, 'get.notfound', key, storage=hook_storage)
        raise exceptions.NotFoundException

    plugin.call_hooks(stype, 'get.postget', key, obj, storage=hook_storage)
    return obj


def update(stype, key, data):
    '''
    Update an object of stype

    @param stype:
    @param key: 
    @param data: C{dict} of data to update object with.
    @raises NotfoundException: If requested object does not exist.
    @return: Instance of L{stype} that was updated.
    '''
    hook_storage = dict()
    store = stormy.Stormy()
    obj = store.get(stype, key)

    if not obj:
        plugin.call_hooks(stype, 'update.notfound', key, storage=hook_storage)
        raise exceptions.NotFoundException

    plugin.call_hooks(stype, 'update.preset', obj, data, storage=hook_storage)

    if hook_storage.get('do_set', True) is not False:
        stormy.dict_set(obj, data)

    plugin.call_hooks(stype, 'update.precommit', obj, storage=hook_storage)

    if hook_storage.get('do_commit', True) is not False:
        store.commit()

    plugin.call_hooks(stype, 'update.postcommit', obj, storage=hook_storage)
    return obj


def delete(stype, key):
    '''
    Remove a storm object
    
    @param stype:
    @param key:
    @return:
    '''
    hook_storage = dict()
    store = stormy.Stormy()
    obj = store.get(stype, key)

    if not obj:
        plugin.call_hooks(stype, 'delete.notfound', obj, storage=hook_storage)
        raise exceptions.NotFoundException

    plugin.call_hooks(stype, 'delete.preremove', obj, storage=hook_storage)
    store.remove(obj)
    plugin.call_hooks(stype, 'delete.precommit', obj, storage=hook_storage)
    store.commit()
    plugin.call_hooks(stype, 'delete.postcommit', obj, storage=hook_storage)
    return obj


def replace(stype, key_name, key_value, data):
    '''
    Replace an object

    @param stype:
    @param key_name:
    @param key_value:
    @param data:
    @return:
    '''
    hook_storage = dict()
    store = stormy.Stormy()
    obj = store.get(stype, key_value)

    if not obj:
        plugin.call_hooks(stype, 'replace.notfound', key_value,
                           storage=hook_storage)
        raise exceptions.NotFoundException

    plugin.call_hooks(stype, 'replace.preremove', obj, storage=hook_storage)
    store.remove(obj)
    data[key_name] = key_value
    return create(stype, data)
