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
Woodstove Logging system
'''

import logging
import logging.handlers

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        ''' '''
        def handle(self, record):
            ''' '''

        def emit(self, record):
            ''' '''

        def createLock(self):
            ''' '''
            self.lock = None


def setup(name=None, lvl=None):
    '''
    Setup the logging system

    @keyword name: Name of the logger to setup
    @keyword lvl: Minimum level for this logger
    '''
    if lvl is None:
        lvl = logging.DEBUG

    logger = logging.getLogger(name)
    logger.setLevel(lvl)
    #logger.addHandler(NullHandler())


def get_logger(obj):
    '''
    Get logging object for L{obj}.

    @param obj: Object to get logger for.
    '''
    return logging.getLogger('.'.join((obj.__module__, obj.__name__)))


def add_handler(handler, lvl, name=None, fmt=None):
    '''
    Add a handler to the logger L{name}.

    @param handler:
    @param lvl:
    @keyword name:
    @keyword fmt:
    '''
    logger = logging.getLogger(name)
    handler.setLevel(lvl)

    if fmt:
        handler.setFormatter(logging.Formatter(fmt))

    logger.addHandler(handler)


def add_filter(filter, name=None):
    '''
    Add a filter to the logger L{name}.

    @param filter:
    @keyword name:
    '''
    logger = logging.getLogger(name)
    logger.addFilter(filter)


def to_file(path, lvl, fmt, name=None, **ops):
    '''
    Add a file handler to the logging system.

    @param path:
    @param lvl:
    @param fmt:
    @keyword name:
    @keyword ops:
    '''
    add_handler(logging.handlers.WatchedFileHandler(path, **ops), lvl, name,
                fmt)


def to_console(lvl, fmt, name=None, **ops):
    '''
    Add a console handler to the logging system.

    @param lvl:
    @param fmt:
    @keyword name:
    @keyword ops:
    '''
    add_handler(logging.StreamHandler(**ops), lvl, name, fmt)


def Logger(name):
    '''
    Logger factory.

    @param name: Name of logger
    '''
    return logging.getLogger(name)
