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
'''
Stateful decorators (think singletons... sort of)

*Framework (black magic) code*
Disabling the following pylint warning:
W0212 - We need to access protected class attributes (things that start with
   double underscore).
'''
# pylint: disable=W0212

from functools import wraps
from weakref import WeakKeyDictionary
from threading import current_thread


def memoize(init):
    ''' Argument based state '''

    if init.__name__ != '__init__':
        raise Exception(
            'state decorator can only be used on __init__() method')

    @wraps(init)
    def decorator(self, *args, **kwargs):
        ''' decorated __init__ '''
        arghash = repr(args) + repr(kwargs)
        try:
            state = self.__class__._state
        except AttributeError:
            state = self.__class__._state = {}
        try:
            self.__dict__ = state[arghash]
        except KeyError:
            state[arghash] = self.__dict__
            init(self, *args, **kwargs)
        try:
            self.__getattribute__('__stateinit__')(*args, **kwargs)
        except AttributeError:
            pass
    return decorator


def stateful(init):
    ''' State decorator for __init__ '''

    if init.__name__ != '__init__':
        raise Exception(
            'state decorator can only be used on __init__() method')

    @wraps(init)
    def decorator(self, *args, **kwargs):
        ''' decorated __init__ '''
        try:
            self.__dict__ = self.__class__._state
        except AttributeError:
            self.__class__._state = self.__dict__
            init(self, *args, **kwargs)
        try:
            self.__getattribute__('__stateinit__')(*args, **kwargs)
        except AttributeError:
            pass
    return decorator


def threadstate(init):
    '''
    Load existing state for this thread or create a new one.
    Used in __init__() of child class.
    '''

    if init.__name__ != '__init__':
        raise Exception(
            'threadstate decorator can only be used on __init__() method')

    @wraps(init)
    def decorator(self, *args, **kwargs):
        ''' init decorator '''
        thread_id = current_thread()
        try:
            state = self.__class__._state
        except AttributeError:
            state = self.__class__._state = WeakKeyDictionary()
        try:
            self.__dict__ = state[thread_id]
        except KeyError:
            state[thread_id] = self.__dict__
            init(self, *args, **kwargs)
        try:
            self.__getattribute__('__stateinit__')(*args, **kwargs)
        except AttributeError:
            pass
    return decorator
