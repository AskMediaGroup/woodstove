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
Exception handler system for api methods.
'''

import bottle
import traceback
from storm.exceptions import DisconnectionError
from woodstove.common import logger
from woodstove.db import stormy
from woodstove import exceptions, app


__exc_handlers__ = None


def register_exc_handler(extype, handler):
    '''
    Register a new exception handler for exception type L{extype}.

    @param extype: Exception type for this handler.
    @param handler: Handler function.
    '''
    global __exc_handlers__

    if __exc_handlers__ is None:
        __exc_handlers__ = dict()

    __exc_handlers__[extype] = handler


def generic_handler(code, message=None, log=None, callback=None):
    '''
    Return a handler function that will use the code, message, log, and
    callback arugments to respond to an exception.

    >>> a = generic_handler(400, 'Bad client! Bad!', 'No biscut for client',
    ...     lambda x, y: logger.Logger(__name__).error('Something else!'))

    @param code: HTTP status code to use in response.
    @keyword message: Message to place in API response object.
    @keyword log: Message to place in the log.
    @keyword callback: Optional function to call during exception handling.
    @return: New handler function.
    '''
    def handler(execp, func):
        '''
        Handler closure that outputs log message, sets HTTP response code,
        calls L{callback} if specified, and formats a response object.

        @param execp: Exception object.
        @param func: Function that caused the exception.
        @return: API Response object.
        '''
        lmessage = message if message else execp.message
        llog = log if log else "%s: %s" % (execp.__class__.__name__,
                                           execp.message)
        logger.Logger(__name__).error(llog)
        bottle.response.status = code

        if callback is not None:
            callback(execp, func)

        return app.response(lmessage, 'failure')

    return handler


default_handler = generic_handler(500, 'Internal Error',
                                  callback=lambda x, y: logger.Logger(__name__).error(
                                      traceback.format_exc()))


def run_exc_handler(execp, func):
    '''
    Run the correct exception handler for L{execp}. If no matching handler is
    found the L{default_handler} is used.

    @param execp: Exception object.
    @param func: Route function that raised the exception.
    '''
    if __exc_handlers__ is None:
        exc_setup()

    handler = __exc_handlers__.get(execp.__class__, default_handler)
    return handler(execp, func)


def exc_setup():
    '''
    Do inital exception handler setup.
    '''
    register_exc_handler(exceptions.ArgumentException, generic_handler(400))
    register_exc_handler(exceptions.AuthException,
                         generic_handler(401, "Not Authorized"))
    register_exc_handler(exceptions.NotFoundException,
                         generic_handler(404, 'Not found'))
    register_exc_handler(exceptions.RequestException,
                         generic_handler(400))
    register_exc_handler(DisconnectionError,
                         generic_handler(500,
                                         'Internal Error',
                                         'Database connection lost!',
                                         lambda *_: stormy.Stormy().reset_timeouts()))
    register_exc_handler(exceptions.InternalException,
                         generic_handler(500, 'Internal Error'))
