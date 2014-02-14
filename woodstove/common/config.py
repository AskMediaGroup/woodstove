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
''' Handle configuration loading '''

import os
import yaml

from woodstove.common import stateful

CONFIG_SEARCH_PATH = [
    os.environ.get('WOODSTOVE_PATH', './conf.d'),
    '/etc/woodstove/conf.d'
]


class Config(object):  # pylint: disable=R0903
    ''' Configuration class '''

    @stateful.memoize
    def __init__(self, conf_file=None, parent=None, data=None):
        ''' Open conf_file '''
        self.conf_file = conf_file
        self.parent = parent
        if data:
            self.dict = self._load_data(data)
        else:
            self.dict = {}
            if conf_file:
                self._find_and_load(conf_file)
            else:
                self.load_app_conf('woodstove')

    def _load_file(self, filep, app):
        ''' Load config data from file '''
        try:
            data = yaml.load(filep)
        except ValueError:
            return
        conf = self._load_data(data)
        self.dict[app] = Config(parent='root', data=conf)

    def _load_data(self, data):
        ''' setup data values '''
        conf = {}
        for key, value in data.iteritems():
            if isinstance(value, dict):
                conf[key] = Config(key, self.conf_file, value)
            else:
                conf[key] = value
        return conf

    def _find_and_load(self, app):
        ''' use search path to find config file '''
        for path in CONFIG_SEARCH_PATH:
            try:
                with open(path + '/' + app + '.yml', 'r') as filep:
                    self._load_file(filep, app)
                break
            except IOError:
                continue

    def load_app_conf(self, appname):
        ''' Attempt to load an apps config file '''
        self._find_and_load(appname)

    def __getattr__(self, name):
        ''' get key from dict '''
        return self.dict[name]

    def __getitem__(self, name):
        ''' get key '''
        return self.dict[name]
