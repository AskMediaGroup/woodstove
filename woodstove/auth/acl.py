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
ACL Interface
'''

import traceback
from woodstove import exceptions
from woodstove.common import config, boolean, logger


class Rule(boolean.Operand):
    '''
    Base ACL Rule class
    '''

    def evaluate(self, user, request, opts):
        '''
        Interface definition for ACL rules.

        @param user: User making the request
        @param request: Bottle request instance
        @keyword opts: Route specific options
        @raise NotImplementedError: Rule class should not be used directly.
        '''
        raise NotImplementedError


class Group(Rule):
    '''
    Group membership rule
    '''

    def __init__(self, group):
        '''
        Setup the rule by saving the group name to check.

        @param group: The group that will be matched against.
        '''
        self.group = group

    def evaluate(self, user, request, opts):
        '''
        Verify L{user} is a member of L{group}.

        @param user: User making the request
        @param request: Bottle request instance
        @keyword opts: Route specific options
        '''
        return self.group in user.groups()


class Superuser(Group):
    '''
    Ensure the user is a `superuser` as per the group name in the woodstove
    configuration section woodstove.groups.superuser.
    '''

    def __init__(self):
        '''
        Read configuation file and call parent class init.
        '''
        conf = config.Config().woodstove.groups
        super(Superuser, self).__init__(conf.superuser)


class ACL(object):
    '''
    Base ACL class
    '''

    def __init__(self, expr):
        '''
        Setup the ACL

        @keyword expr: ACL rule expression
        '''
        self.expr = expr

    def verify(self, user, request, opts=None):
        '''
        Ensure the user/request match the rules defined in this ACL.

        @param user: User making the request
        @param request: Bottle request instance
        @keyword opts: Route specific options
        '''
        try:
            if not self.expr.evaluate(user, request, opts):
                raise exceptions.AuthException
        except exceptions.AuthException:
            msg = "ACL Rules not matched: %r" % self.expr
            logger.Logger(__name__).debug(msg)
            raise
        except exceptions.NotFoundException:
            raise
        except Exception:
            logger.Logger(__name__).debug(traceback.format_exc())
            raise exceptions.AuthException
