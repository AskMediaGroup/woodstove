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
Provides functions to load apps and setup bottle apps
'''

import bottle
import json
import traceback
from woodstove.common import logger, config#, context
from woodstove import app


__apps__ = []


# pylint for some reason can't find the error decorator in the bottle module
@bottle.error(404)  # pylint: disable=E1101
def error404(_):
    ''' HTTP 404 handler '''
    msg = "404 Not found: %s %s" % (bottle.request.method, bottle.request.path)
    logger.Logger(__name__).debug(msg)
    return json.dumps(app.response(msg, 'failure'))


@bottle.error(500)  # pylint: disable=E1101
def error500(_):
    ''' HTTP 500 handler '''
    msg = "500 Internal Error: %s %s" % (bottle.request.method,
                                         bottle.request.path)
    logger.Logger(__name__).debug(msg)
    return json.dumps(app.response(msg, 'failure'))


def load_config():
    '''
    Load configuration for all loaded apps.
    '''
    for app_name in config.Config().woodstove.apps:
        config.Config().load_app_conf(app_name)


def setup_logging():
    '''
    Configure logging for woodstove.
    '''
    conf = config.Config().woodstove.logging
    logger.setup()#lvl=conf.level)
    #logger.add_filter(context.ContextFilter())
    logger.to_file(conf.file, None, conf.format) # conf.level, conf.format)


def import_apps(apps, app_module=True):
    '''
    Load app modules

    @param apps:
    @keyword app_module:
    @return:
    '''
    modules = list()
    fromlist = list()

    if app_module:
        fromlist = ['app']

    for app_name in apps:
        try:
            modules.append(__import__(app_name, fromlist=fromlist))
        except BaseException:  # pylint: disable=W0703
            logger.Logger(__name__).error("Unable to import: %s" % app)
            logger.Logger(__name__).debug(traceback.format_exc())

    return modules


def mount_apps():
    ''' Attach apps to root '''
    for klass in app.get_apps():  # pylint: disable=E1101
        obj = klass()

        try:
            app_obj = obj.mount()
        except Exception:
            logger.Logger(__name__).error("Unable to mount: %r" % klass)
            logger.Logger(__name__).debug(traceback.format_exc())
            continue

        __apps__.append(obj)
        logger.Logger(__name__).debug("Mouting %r (%r) at %s%s" % (obj,
                                      app_obj, obj.namespace, obj.path))
        bottle.default_app().mount("%s%s" % (obj.namespace, obj.path), app_obj)
