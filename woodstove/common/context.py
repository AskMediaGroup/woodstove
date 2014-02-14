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
Thread context managment.
'''


import threading
import copy


def ctx_push(ctx):
    '''
    Push a new context dict to the current threads context stack.

    @param ctx: C{dict} containing new context information.
    '''
    thread = threading.currentThread()

    try:
        thread.context.append(ctx)
    except AttributeError:
        thread.context = [ctx]


def ctx_pop():
    '''
    Pop a context C{dict} from the current threads context stack.

    @return: The C{dict} that was removed or None if no contexts on stack.
    '''
    thread = threading.currentThread()

    try:
        return thread.context.pop()
    except AttributeError:
        thread.context = list()
    except IndexError:
        # Ignore requests to pop an empty context.
        pass


def ctx_get():
    '''
    Get the top of the context stack without removing it from the stack.

    @return: The C{dict} on the top of the stack or None if stack is empty.
    '''
    thread = threading.currentThread()

    try:
        return thread.context
    except AttributeError:
        return


def ctx_copy():
    '''
    Copy and ceturn the context stack.

    @return: Deepcopy of the context stack or None if stack is empty.
    '''
    thread = threading.currentThread()

    try:
        return copy.deepcopy(thread.context)
    except AttributeError:
        return


class Context(object):
    '''
    Context manager for adding a context dict to a block.
    '''
    def __init__(self, **kwargs):
        '''
        Setup the context.

        @keyword **kwargs: Values to be added to the context.
        '''
        self.ctx = kwargs

    def __enter__(self):
        '''
        Push new context C{dict} onto stack.
        '''
        ctx_push(self.ctx)

    def __exit__(self, *_):
        '''
        Pop context C{dict} off stack.
        '''
        ctx_pop()


class ContextFilter(object):
    '''
    Add thread context data to log record.
    '''
    def filter(self, record):
        '''
        Pull context data and insert it into L{record}.

        @param record: Log record to update
        '''
        record.__dict__['context'] = {}

        for ctx in ctx_get():
            record.context.update(ctx)

        return True
