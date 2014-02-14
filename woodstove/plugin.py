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
''' Plugin system '''


import traceback
from woodstove.common import logger, config


__hooks__ = dict()
__plugins__ = list()


def load_plugins():
    '''
    Load all plugin modules defined in configuration file.
    '''
    conf = config.Config().woodstove
    log = logger.Logger(__name__)

    for plugin in conf.plugins:
        try:
            __plugins__.append(__import__(plugin))
        except BaseException:
            log.error("Error importing plugin: %s" % plugin)
            log.debug(traceback.format_exc())


def get_hook_table(name):
    ''' Get the hook table 'name' or create the table if it does not exist '''
    return __hooks__.setdefault(name, dict())


def register_hook(table_name, hook_name, func):
    ''' Register `func` as in the `hook_name` hook in the `table_name`
        table '''
    table = get_hook_table(table_name)
    hook = table.setdefault(hook_name, set())
    hook.add(func)


def remove_hook(table_name, hook_name, func):
    ''' Remove `func` from the `hook_name` hook in the `table_name`
        table '''
    table = get_hook_table(table_name)
    hook_table = table.setdefault(hook_name, set())
    hook_table.discard(func)


def hook(table, name):
    '''
    Decorator version of register hook

    @param table: Table to add hook to.
    @param name: Name of hook.
    '''
    def decorator(func):
        '''
        Register hook and return original function.

        @param func: Function being added to hook table.
        @return: Original function.
        '''
        register_hook(table, name, func)
        return func

    return decorator


def call_hooks(table_name, hook_name, *args, **kwargs):
    '''
    Call all the `name` hooks in `table`
    
    @param table_name: Table to run hooks from.
    @param hook_name: Name of hook.
    @param *args: Positional arguments to pass into hook functions.
    @param **kwargs: Keyword arguments to pass into hook functions.
    @raise Exception: Any exceptions raised by the hooks will be logged and
        reraised by this function.
    '''
    table = get_hook_table(table_name)
    for hook in table.get(hook_name, list()):
        try:
            hook(*args, **kwargs)
        except BaseException as execp:
            logger.Logger(__name__).error("%r exception in hook %r" % (execp,
                                                                       hook))
            raise
