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
A simple authentication adapter using the main woodstove database.
'''

from hmac import HMAC as hmac
from hashlib import sha256
from storm.locals import Unicode, ReferenceSet, Storm, Int
from woodstove import exceptions
from woodstove.auth import adapter
from woodstove.db import stormy


class AuthGroup(Storm):
    ''' Auth group ORM model '''

    #pylint: disable=R0903

    __storm_table__ = 'auth_group'

    id = Int(primary=True)
    name = Unicode()
    users = ReferenceSet('AuthGroup.id',
                         'AuthGroupMap.group_id',
                         'AuthGroupMap.user_id',
                         'AuthUser.id')


class AuthGroupMap(Storm):
    ''' Auth Group/User map ORM model '''

    #pylint: disable=R0903

    __storm_table__ = 'auth_user_map'
    __storm_primary__ = 'user_id', 'group_id'

    user_id = Int()
    group_id = Int()


class AuthUser(Storm):
    ''' Auth user ORM modes '''

    #pylint: disable=R0903

    __storm_table__ = 'auth_user'

    id = Int(primary=True)
    name = Unicode()
    passwd = Unicode()
    groups = ReferenceSet('AuthUser.id',
                          'AuthGroupMap.user_id',
                          'AuthGroupMap.group_id',
                          'AuthGroup.id')


class DBUserAdapter(adapter.UserAdapter):
    ''' Simple database backed auth adapter '''
    def groups(self, name):
        ''' list all groups the user `name` is in '''
        user = self.get_user(name)
        if not user:
            raise exceptions.LoginException()

        return (x.name for x in user.groups)

    def get_user(self, name):
        ''' look up the user `name` '''
        return stormy.Stormy().find(AuthUser, AuthUser.name == name).one()

    def remove_user(self, name):
        ''' remove the user `name` '''
        user = self.get_user(name)
        if not user:
            raise Exception()
        stormy.Stormy().remove(user)
        # TODO - make sure to remove all references to this user in the user/
        # group map table.
        stormy.Stormy().commit()

    def add_group(self, name):
        ''' add the group `name` '''
        group = AuthGroup()
        group.name = name
        stormy.Stormy().add(group)
        stormy.Stormy().commit()
        return group

    def get_group(self, name):
        ''' look up the group `name` '''
        return stormy.Stormy().find(AuthGroup, AuthGroup.name == name).one()

    def remove_group(self, name):
        ''' remove the group `name` '''
        group = self.get_group(name)
        if not group:
            raise Exception()
        stormy.Stormy().remove(group)
        # TODO - make sure to remove all references to this group in the user/
        # group map table.
        stormy.Stormy().commit()

    def passwd_hash(self, user, passwd):
        ''' perform password hashing '''
        salt = self.conf.db.salt
        return unicode(hmac(salt, user + passwd, sha256).hexdigest())

    def user(self, name, passwd):
        ''' does the name/password combo match a user in the db? '''
        pwhash = self.passwd_hash(name, passwd)

        user = self.get_user(name)
        if not user:
            return False

        return user.passwd == pwhash

    def add_user(self, name, passwd, groups=None):
        ''' add a user '''
        user = AuthUser()
        user.name = name
        user.passwd = self.passwd_hash(name, passwd)
        if groups:
            for group_name in groups:
                group = self.get_group(group_name)
                if group:
                    user.groups.add(group)

        stormy.Stormy().add(user)
        stormy.Stormy().commit()
        return user

    def add_to_group(self, name, groupname):
        ''' add the user `name` to the group `groupname` '''
        user = self.get_user(name)
        group = self.get_group(groupname)

        user.groups.add(group)
        stormy.Stormy().commit()

    def remove_from_group(self, name, groupname):
        ''' remove the user `name` from the group `groupname` '''
        user = self.get_user(name)
        group = self.get_group(groupname)

        user.groups.remove(group)
        stormy.Stormy().commit()


class DBLoginAdapter(adapter.LoginAdapter):
    '''
    '''

    def login(self, name, request):
        '''
        '''


adapter.UserAdapter.register('db', DBUserAdapter)
adapter.LoginAdapter.register('db', DBLoginAdapter)
