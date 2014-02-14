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
Boolean expression support.

NOTE: Using evaluate() method instead of using __nonzero__() to allow the user
of this module to pass arguments to the evaluate() method of all the objects in
the expression.
'''


class Operand(object):
    '''
    Boolean expression operand
    '''

    def __and__(self, other):
        '''
        Support AND (&) operator

        @param other:
        '''
        return And(self, other)

    def __or__(self, other):
        '''
        Support OR (|) operator

        @param other:
        '''
        return Or(self, other)

    def __invert__(self):
        '''
        Support NOT (~) operator
        '''
        return Not(self)


class UnaryOper(Operand):
    '''
    Unary operator base class.
    '''

    def __init__(self, value):
        '''

        @param value:
        '''
        self.value = value


class BinaryOper(Operand):
    '''
    Binary operator base class.
    '''

    def __init__(self, left, right):
        '''

        @param left:
        @param right:
        '''
        self.left = left
        self.right = right


class And(BinaryOper):
    '''
    AND (&) Operator
    '''

    def evaluate(self, *args, **kwargs):
        '''
        Evaluate expression

        @return:
        '''
        return (self.left.evaluate(*args, **kwargs)
                and self.right.evaluate(*args, **kwargs))


class Or(BinaryOper):
    '''
    OR (|) Operator
    '''

    def evaluate(self, *args, **kwargs):
        '''
        Evaluate expression

        @return:
        '''
        return (self.left.evaluate(*args, **kwargs)
                or self.right.evaluate(*args, **kwargs))


class Not(UnaryOper):
    '''
    NOT (~) Operator
    '''

    def evaluate(self, *args, **kwargs):
        '''
        Evaluate expression

        @return:
        '''
        return not self.value.evaluate(*args, **kwargs)
