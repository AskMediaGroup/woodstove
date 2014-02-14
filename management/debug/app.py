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
''' Debug app '''


import time
from woodstove.app import app
from woodstove.common import logger


def ping(job=None):  # pylint: disable=W0613
    ''' Ping/Pong '''
    logger.Logger(__name__).info("PONG")


@app.path('/debug')
class Debug(app.App):
    ''' debug app '''

    @app.get('/ping')
    def ping(self):
        '''
         Create a job and put it on the queue
        '''
        return self.response(self.async(ping))

    @app.get('/auth')
    def check_auth(self):
        '''
        Test authentication
        '''
        self.auth()
        return self.response([])

    @app.get('/time')
    def time(self):
        '''
        Get current server time
        '''
        return self.response(int(time.time()))
