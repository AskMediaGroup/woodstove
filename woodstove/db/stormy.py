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
''' Storm related stuff '''

import time
import datetime
from storm.locals import create_database, Store, And, Desc
from storm.expr import BinaryOper, compile as storm_compile
from storm.info import get_cls_info
from storm.store import ResultSet
from storm.references import BoundReferenceSet
from storm.tracer import debug
from storm.exceptions import DisconnectionError, ClassInfoError
from woodstove import exceptions
from woodstove.common import logger, config, stateful


def inspect(cls):
    '''
    Get details about the column information from a Storm ORM class.

    @param cls: The class to inspect.
    @return:
    @raise InternalException: If L{cls} is not a Storm class.
    '''
    try:
        info = get_cls_info(cls)
    except ClassInfoError:
        raise exceptions.InternalException("%r is not a storm class." % cls)

    for name, column in info.attributes.iteritems():
        # BLACK MAGIC:
        # To get access to the original property object after storm has done
        # its class wiring is a bit of a challenge. The following is the least
        # difficult to follow way of doing it.
        #
        # When storm wires up the class it replaces the property instances in
        # the class with column objects. These object don't have any direct
        # way of referencing the original property object. However storm
        # replaces the __get__, __set__, and __delete__ methods of the new
        # column object with the coresponding methods of the property object.
        # We can use that fact to get access to the original object through
        # column object by way of the C{im_self} attribute of the __get__
        # method.
        prop = column.__get__.im_self
        yield (name, column, prop)


def storm_to_dict(obj):
    '''
    Transform storm result object into dict

    @param obj: Storm object to convert to C{dict}.
    @return: C{dict} representation of storm object.
    @raise TypeError: If L{obj} is not a storm object.
    '''
    if not hasattr(obj, "__storm_table__"):
        raise TypeError(repr(obj) + " is not JSON serializable!!!")

    result = {}

    for name, column, property in inspect(obj.__class__):
        try:
            if property._stove_hidden:
                continue
        except AttributeError:
            pass

        result[name] = getattr(obj, name)

        if isinstance(result[name], datetime.datetime):
            result[name] = str(result[name])

        if callable(result[name]):
            result[name] = result[name].__name__

    return result


def storm_set_to_dict(obj):
    '''
    Transform store result set or reference object into list of dicts.

    @param obj: Storm object to convert to C{dict}.
    @return: C{dict} representation of storm object.
    @raise TypeError: If L{obj} is not a storm resultset or reference object.
    '''
    if type(obj) not in (ResultSet, BoundReferenceSet):
        raise TypeError(type(obj) + repr(obj) + " is not JSON serializable!!!")

    result = []

    for item in obj:
        result.append(storm_to_dict(item))

    return result


class Regex(BinaryOper):  # pylint: disable=R0901
    ''' MySQL regexp operator for storm '''
    __slots__ = ()
    oper = " REGEXP "


@storm_compile.when(Regex)
def compile_regex(compiler, expr, state):
    ''' Compile Regex operator '''
    return "IFNULL(%s, '') REGEXP %s" % (compiler(expr.expr1, state),
                                         compiler(expr.expr2, state))


storm_compile.set_precedence(30, Regex)


def dict_set(obj, data):
    ''' Helper function for setting storm values from a dict '''
    for field, value in data.items():
        obj.__setattr__(field, value)
    return obj


def gen_expr(stype, data):
    ''' '''
    expr = None

    for column in get_cls_info(stype).columns:
        try:
            regex = data[column.name]
        except KeyError:
            continue

        if not regex:
            raise exceptions.RequestException("Empty regex in query")

        cur = Regex(column, regex)
        expr = And(expr, cur) if expr else cur

    return expr


class Query(object):
    '''
    DB Query
    '''
    table = None
    order = None
    using = None
    where = None
    offset = None
    distinct = False
    desc = False
    _limit = None
    _results = None

    def __init__(self, table):
        '''
        @param table:
        '''
        self.table = table

    @property
    def limit(self):
        '''
        '''
        if self._limit is not None:
            return self._limit + self.offset

    @limit.setter
    def limit(self, value):
        '''
        @param value:
        '''
        self._limit = value

    @property
    def results(self):
        '''
        '''
        if not self._results:
            store = Stormy()

            if self.using:
                store = store.using(*self.using)

            if self.where:
                self._results = store.find(self.table, self.where)
            else:
                self._results = store.find(self.table)
           
            if self.order:
                order = self.order

                if self.desc:
                    order = Desc(order)

                self._results = self._results.order_by(order)

            self._results.config(distinct=self.distinct)

        return self._results

    def execute(self):
        '''
        '''
        return (self.results[self.offset:self.limit], self.results.count())


class Stormy(object):  # pylint: disable=R0903
    ''' Stateful class for accessing storm '''

    # pylint: disable=W0212

    __database = None

    @stateful.threadstate
    def __init__(self, dsn=None):
        ''' Setup or fetch state '''
        self.conf = config.Config().woodstove.storm
        if not self.__class__.__database:
            if not dsn:
                dsn = self.conf.dsn

            if self.conf.debug:
                debug(True, stream=open(self.conf.file, 'a+'))

            self.__class__.__database = create_database(dsn)
        self.store = Store(self.__class__.__database)
        self.poke = time.time()

    def __stateinit__(self, dsn=None):  # pylint: disable=W0613
        ''' per instance setup '''
        now = time.time()

        try:
            self.store._connection._ensure_connected()
            if now - self.poke > 14400:
                self.store.execute("DO 0", noresult=True)
        except DisconnectionError:
            msg = "Lost connection to database reconnecting"
            logger.Logger(__name__).warn(msg)
            self.store.rollback()

        self.poke = now

    def __getattr__(self, name):
        ''' pass request into storm '''
        return getattr(self.store, name)

    def reset_timeouts(self):
        ''' reset poke value to 0 '''
        self.poke = 0


def required(obj, funcs=None):
    ''' setup required for `obj` '''
    if not funcs:
        funcs = ('create', 'replace')

    obj._stove_required = True
    obj._stove_required_funcs = funcs
    return obj


def matches(obj, pattern, funcs=None):
    ''' setup matches for `obj` '''
    if not funcs:
        funcs = ('create', 'replace', 'update')

    obj._stove_regex = pattern
    obj._stove_regex_funcs = funcs
    return obj


def hidden(obj):
    ''' Flag obj as hidden '''
    obj._stove_hidden = True
    return obj
