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
''' CRUD App mixin '''


from woodstove.db import stormy, generic
from woodstove.auth import acl, ownership, user
from woodstove.app import arguments


OWNER_ARGS = arguments.ArgumentList([
    arguments.Bool('grant', default=False, desc='Give new owner grant privlages to the object'),
])


class Ownership(object):
    '''
    '''
    ownership_class = None
    ownership_key_type = None

    @get('/:key/owners/users')
    def read_user_owners(self, key):
        ''' Get list of owners of this pool '''
        self.auth(acl.ACL(ownership.Owner(self.ownership_class) | acl.Superuser()),
                  object_id=self.ownership_key_type(key))
        pool = generic.read(self.ownership_class, self.ownership_key_type(key))

        def format(user_obj):
            '''
            '''
            return {'user_id': user_obj.user_id,
                    'grant': ''}

        users = [format(u) for u in ownership.Owners(pool).users]
        return self.response(users)

    @put('/:key/owners/users/:user_id')
    def create_user_owner(self, key, user_id):
        ''' '''
        self.auth(acl.ACL(ownership.Owner(self.ownership_class, grant=True) | acl.Superuser()),
                  object_id=self.ownership_key_type(key))
        pool = generic.read(self.ownership_class, self.ownership_key_type(key))
        grant = self.validate(OWNER_ARGS)['grant']
        user_obj = generic.get(user.User, int(user_id))
        ownership.add_owning_user(pool, user_obj, grant=grant)
        stormy.Stormy().commit()
        return self.response(list())

    @delete('/:key/owners/users/:user_id')
    def delete_user_owner(self, key, user_id):
        ''' '''
        self.auth(acl.ACL(ownership.Owner(self.ownership_class, grant=True) | acl.Superuser()),
                  object_id=self.ownership_key_type(key))
        pool = generic.read(self.ownership_class, self.ownership_key_type(key))
        ownership.remove_owning_user(pool, int(user_id))
        stormy.Stormy().commit()
        return self.response(list())

    @get('/:key/owners/groups')
    def read_group_owners(self, key):
        ''' Get list of owners of this pool '''
        self.auth(acl.ACL(ownership.Owner(self.ownership_class) | acl.Superuser()),
                  object_id=self.ownership_key_type(key))
        pool = generic.read(self.ownership_class, self.ownership_key_type(key))
        groups = ownership.get_owning_groups(pool)
        return self.response(groups)

    @put('/:key/owners/groups/:group')
    def create_group_owner(self, key, group):
        self.auth(acl.ACL(ownership.Owner(self.ownership_class, grant=True) | acl.Superuser()),
                  object_id=self.ownership_key_type(key))
        grant = self.validate(OWNER_ARGS)['grant']
        pool = generic.read(self.ownership_class, self.ownership_key_type(key))
        ownership.add_owning_group(pool, self.ownership_key_type(group), grant=grant)
        stormy.Stormy().commit()
        return self.response(list())

    @delete('/:key/owners/groups/:group')
    def delete_group_owner(self, key, group):
        ''' '''
        self.auth(acl.ACL(ownership.Owner(self.ownership_class, grant=True) | acl.Superuser()),
                  object_id=self.ownership_key_type(key))
        pool = generic.read(self.ownership_class, self.ownership_key_type(key))
        ownership.remove_owning_group(pool, self.ownership_key_type(group))
        stormy.Stormy().commit()
        return self.response(list())
