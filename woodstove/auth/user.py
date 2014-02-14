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
''' User '''

from storm.locals import (Unicode, Int, DateTime, Storm, ReferenceSet, Bool,
                          JSON)
from woodstove.db import stormy
from woodstove.auth import adapter


class User(Storm):
    '''
    ORM for woodstove users. This class is used in addition to the AuthAdapter
    interface to provide a way to assign ownership of database object to a
    specific user independently of how the "real" user information is stored.

    @ivar user_id:
    @ivar name:
    @ivar created:
    @ivar active:
    @ivar jobs:
    @ivar private: Storage for handlers to keep aditional data about a user.
    '''

    __storm_table__ = 'woodstove_user'

    _adapter = None

    user_id = Int(primary=True)
    name = Unicode()
    created = DateTime()
    active = stormy.required(Bool())
    private = stormy.hidden(JSON())
    jobs = ReferenceSet(user_id, 'Job.user_id')

    @property
    def adapter(self):
        '''
        Get instance of current AuthAdapter class.

        @return:
        '''
        if self._adapter is None:
            self._adapter = adapter.AuthAdapter()

        return self._adapter

    def groups(self):
        '''
        Get the groups this user is in.

        @return: List of groups user is a member of.
        '''
        return self.adapter.groups(self)

    def exists(self):
        '''
        Verify with auth adapter that this user exists.

        @return: C{bool}
        '''
        exists = self.adapter.exists(self)

        if not exists:
            self.active = False

        return exists
