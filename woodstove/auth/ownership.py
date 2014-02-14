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
Object ownership system.
'''


from storm import info
from storm.locals import Storm, Reference, Unicode, Int, JSON, Pickle, Bool
from woodstove import exceptions
from woodstove.db import stormy, generic
from woodstove.auth import user, acl


class Ownership(Storm):
    '''
    ORM for an ownership record.

    @ivar ownership_id: Database primary key
    @ivar user_id: ID of user for this ownership.
    @ivar group_name: Name of group for this ownership.
    @ivar klass: Owned object type.
    @ivar object_id: ID of owned object.
    @ivar private: Can be used by application to store additional data related
        to this ownership record.
    '''
    __storm_table__ = 'woodstove_ownership'

    ownership_id = Int(primary=True)
    user_id = Int()
    group_name = Unicode()
    klass = Pickle()
    object_id = Pickle()
    object_id_name = Unicode()
    grant = Bool()
    private = JSON()
    user = Reference(user_id, user.User.user_id)

    def __init__(self, object):
        '''
        Setup ownership record.

        @param object: Owned object.
        '''
        obj_id, obj_id_name = get_object_info(object)
        self.klass = object.__class__
        self.object_id = obj_id
        self.object_id_name = unicode(obj_id_name)


def get_object_info(object):
    '''
    Extract information from storm object.

    @param object: Object to inspect.
    @return: C{tuple} of L{objects} ID value and ID field name.
    '''
    klass_info = info.get_cls_info(object.__class__)

    if len(klass_info.primary_key) != 1:
        raise exceptions.InternalException("Ownership does not support"
                                           "composed primary keys!")

    object_id_prop = klass_info.primary_key[0]
    object_id_name = object_id_prop.name
    object_id = getattr(object, object_id_name)

    return (object_id, object_id_name)


def get_object(ownership):
    '''
    Get the object referenced by L{ownership}.

    @param ownership: Ownership object
    @return: Instance of ownership.klass referenced by ownership.object_id.
    '''
    klass = ownership.klass
    object_id = getattr(klass, ownership.object_id_name)
    return stormy.Stormy().find(klass, object_id == ownership.object_id).one()


def get_objects_owned_by_user(klass, user_obj):
    '''
    Get all objects of type L{klass} owned by user.

    @param klass: Object type to lookup.
    @param user_obj: Owning user.
    @return: List of objects owned by user.
    '''
    ownerships = get_user_ownerships(user_obj)
    return [get_object(x)
            for x
            in ownerships.find(Ownership, Ownership.klass == klass)]


def get_objects_owned_by_group(klass, group):
    '''
    Get all objects of type L{klass} owned by group.

    @param klass: Object type to lookup.
    @param group: Owning group name.
    @return: List of objects owned by group.
    '''
    ownerships = get_group_ownerships(group)
    return [get_object(x)
            for x
            in ownerships.find(Ownership, Ownership.klass == klass)]


def get_user_ownerships(user_obj):
    '''
    Get all ownership records for a user.

    @param user_obj: Owning user.
    @return: List of ownerships for user.
    '''
    return stormy.Stormy().find(Ownership,
                                Ownership.user_id == user_obj.user_id)


def get_group_ownerships(group):
    '''
    Get all ownership records for a group.

    @param group: Owning group name.
    @return: List of ownerships for group.
    '''
    return stormy.Stormy().find(Ownership,
                                Ownership.group_name == group)


def remove_user_ownerships(user_obj):
    '''
    Remove all ownerships for user.

    @param user_obj: Owning user.
    '''
    get_user_ownerships(user_obj).remove()


def remove_group_ownerships(group):
    '''
    Remove all ownerships for group.

    @param group: Owning group name.
    '''
    get_group_ownerships(group).remove()


def get_owners(object):
    '''
    Get all ownership records for object.

    @param object: Primary key of object.
    @return:
    '''
    object_id, _ = get_object_info(object)

    return stormy.Stormy().find(Ownership, (Ownership.klass == object.__class__
                                & Ownership.object_id == unicode(object_id)))


def reset_owners(object):
    '''
    Remove all ownership records for object.

    @param object: Primary key of object.
    '''
    get_owners(object).remove()


def get_owning_groups(object):
    '''
    Get names of all groups with ownership of L{object}.

    @param object: Object to lookup ownership for.
    @return: List of group names that are owners of L{object}.
    '''
    owners = get_owners(object)
    return [x.group_name for x in owners if x.group_name is not None]


def get_owning_users(object):
    '''
    Get all users with ownershio of L{object}.

    @param object: Object to lookup ownership for.
    @return: List of users that are owners of L{object}.
    '''
    object_id, _ = get_object_info(object)

    return stormy.Stormy().find(user.User, (Ownership.klass == object.__class__
                                & Ownership.object_id == object_id
                                & Ownership.user_id == user.User.user_id))


def add_owning_user(object, user_obj, grant=False, private=None):
    '''
    Add user to owners of L{object}.

    @param object: Primary key of object.
    @param user_obj: User to add to ownership
    @param grant: Can the user grant ownership of this object to others.
    @keyword private: Application specific data for ownership record.
    @return:
    '''
    ownership = Ownership(object)
    ownership.user_id = user_obj.user_id
    ownership.grant = grant

    if private is not None:
        ownership.private = private

    stormy.Stormy().add(ownership)
    return ownership


def add_owning_group(object, group, grant=False, private=None):
    '''
    Add group to owners of L{object}.

    @param object: Primary key of object.
    @param user: User to add to ownership
    @param grant: Can users in this group grant ownership of this object to
        others.
    @keyword private: Application specific data for ownership record.
    @return:
    '''
    ownership = Ownership(object)
    ownership.group_name = user.group
    ownership.grant = grant

    if private is not None:
        ownership.private = private

    stormy.Stormy().add(ownership)
    return ownership


def get_user_ownership(object, user_obj):
    '''
    Get ownership record for user of object.

    @param object: Owned object.
    @param user_obj: Owner.
    @return: Ownership record.
    '''
    object_id, _ = get_object_info(object)

    ownership = stormy.Stormy().find(Ownership,
                                     klass=object.__class__,
                                     object_id=object_id,
                                     user_id=user_obj.user_id).one()

    if not ownership:
        raise exceptions.NotFoundException

    return ownership


def get_group_ownership(object, group):
    '''
    Get ownership record for group of object.

    @param object: Owned object.
    @param group: Owning group.
    @return: Ownership record.
    '''
    object_id, _ = get_object_info(object)

    ownership = stormy.Stormy().find(Ownership, klass=object.__class__,
                                     object_id=object_id,
                                     group_name=user.group).one()

    if not ownership:
        raise exceptions.NotFoundException

    return ownership


def remove_owning_user(object, user_obj):
    '''
    Remove user from owners of L{object}.

    @param object: Owned object.
    @param user_obj: Owning user.
    '''
    get_user_ownership(object, user_obj).remove()


def remove_owning_group(object, group):
    '''
    Remove group from owners of L{object}.

    @param object: Owned object.
    @param group: Owning group.
    '''
    get_group_ownership(object, group).remove()


class Ownable(Storm):
    '''
    Parent class for ownable database objects.
    '''

    __owners = None

    @property
    def owners(self):
        '''
        Property added to class which implements the ownership api.

        @return: Instance of L{Owners}.
        '''
        if self.__owners is None:
            self.__owners = Owners(self)
        return self.__owners


class Owner(acl.Rule):
    ''' '''
    def __init__(self, klass, grant=False):
        '''
        '''
        self.klass = klass
        self.grant = grant
        super(Owner, self).__init__()

    def evaluate(self, user, request, opts):
        '''
        '''
        obj_id = opts.get('object_id')

        if obj_id is None:
            return False

        try:
            obj = generic.get(self.klass, obj_id)
        except exceptions.NotFoundException:
            return False

        try:
            ownership = get_user_ownership(obj, user)

            if self.grant and not ownership.grant:
                return False

            return True
        except exceptions.NotFoundException:
            return False


class Owners(object):
    '''
    Class interface to the ownership api for a specific object type.
    '''
    class Groups(object):
        '''
        Nested class to provide interface to the groups that own the object.
        '''
        def __init__(self, obj):
            '''
            Save reference to the owned object.

            @param obj: Owned object.
            '''
            self.obj = obj

        def __getitem__(self, name):
            '''
            Get ownership record for group L{name}.

            @param name: Owning group.
            '''
            return get_group_ownership(self.obj, name)

        def __delitem__(self, name):
            '''
            Remove a group from the owners of this object.

            @param user_obj: Owning group.
            '''
            return remove_group_ownership(self.obj, name)

        def __setitem__(self, name, private):
            '''
            Add a group as an owner of this object.

            @param name: New owning group.
            @param private: Application private data for ownership record.
            @return: New ownership record.
            '''
            return add_owning_group(self.obj, name, private)

        def __iter__(self):
            '''
            Iterate over all the users that own this object.
            '''
            return get_owning_groups(self.obj)

    class Users(object):
        '''
        Nested class to provide interface to the users that own the object.
        '''
        def __init__(self, obj):
            '''
            Save reference to the owned object.

            @param obj: Owned object.
            '''
            self.obj = obj

        def __getitem__(self, user_obj):
            '''
            Get ownership record for this user.

            @param user_obj: Owning user.
            '''
            return get_user_ownership(self.obj, user_obj)

        def __delitem__(self, user_obj):
            '''
            Remove a user from the owners of this object.

            @param user_obj: Owning user.
            '''
            remove_user_ownership(self.obj, user_obj)

        def __setitem__(self, user_obj, private):
            '''
            Add a user an an owner of this object.

            @param user_obj: New owning user.
            @param private: Application private data for ownership record.
            @return: New ownership record.
            '''
            return add_owning_user(self.obj, user_obj, private)

        def __iter__(self):
            '''
            Iterate over all the users that own this object.
            '''
            return get_owning_users(self.obj)

    __users = None
    __groups = None

    def __init__(self, obj):
        '''
        Save reference to the owned object.

        @param obj: Owned object.
        '''
        self.obj = obj

    def __iter__(self):
        '''
        Iterate over all ownership records for this object.
        '''
        return get_owners(self.obj)

    def reset(self):
        '''
        Remove all existing ownership records for the object.
        '''
        reset_owners(self.obj)

    @property
    def users(self):
        '''
        Get instance of Owners.Users.

        @return: Instance of L{Owners.Users}.
        '''
        if self.__users is None:
            self.__users = self.Users(self.obj)

        return self.__users

    @property
    def groups(self):
        '''
        Get instance of Owners.Groups.

        @return: Instnace of L{Owners.Groups}.
        '''
        if self.__groups is None:
            self.__groups = self.Groups(self.obj)

        return self.__groups
