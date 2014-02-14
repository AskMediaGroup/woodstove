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
AuthAdapter
'''

from woodstove.common import config


class Credentials(object):
    '''
    @ivar name: The name of the user passed by the client.
    @ivar credentials: Opaque value containing the adapter specific
        credentials for the user.
    '''
    def __init__(self, name=None, credentials=None):
        self.name = name
        self.credentials = credentials


class AuthAdapter(object):
    '''
    Base class for authentication adapters.
    '''

    __adapters = dict()

    @classmethod
    def register(cls, name, adapter):
        '''
        register an auth adapter.

        @param name: Name of adapter.
        @param adapter: Adapter class.
        '''
        cls.__adapters[name] = adapter

    def __new__(cls):
        '''
        Return instance of the currently selected adapter.
        '''
        adapter = config.Config().woodstove.auth.adapter
        try:
            return object.__new__(cls.__adapters[adapter])
        except KeyError:
            raise TypeError('No auth adaptor configured')

    def request(self):
        '''
        Extract authentication data from wsgi request.

        @return: L{Credentials} object.
        '''
        raise NotImplementedError

    def verify(self):
        '''
        Verify the credentials passed by the client.

        @return: L{Credentials} object.
        @raise AuthException: If the credentials are invalid.
        '''
        raise NotImplementedError

    def exists(self, name):
        '''
        Check if a user L{name} exists.

        @param name: Name to lookup.
        @return: Bool based of exsitence of user.
        '''
        raise NotImplementedError

    def login(self, user, creds):
        '''
        Perform login operation.

        @param user:
        @param creds:
        @raise AuthException:
        '''
        raise NotImplementedError

    def create(self, user):
        '''
        Create a new user.

        @param user:
        '''
        raise NotImplementedError

    def delete(self, user):
        '''
        Delete an existing user.

        @param user: The user to delete.
        '''
        raise NotImplementedError

    def groups(self, user):
        '''
        Lookup group membership for L{user}.

        @param user: User to find groups for.
        @return: C{list} of group names L{user} is a member of.
        '''
        raise NotImplementedError

    def format(self, user):
        '''
        Format a User object to be sent to the client.

        @param user: User to format.
        @return: formatted user object.
        '''
        return user
