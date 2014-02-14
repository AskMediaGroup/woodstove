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
Argument validator

    >>> arguments = ArgumentList([
    ...     Argument('foo', (int,)),
    ...     Argument('bar', (unicode, str)),
    ... ])
    >>> arguments.validate({
    ...     'foo': 1,
    ...     'bar': 'baz',
    ... })
    >>> arguments.validate({
    ...     'foo': 1,
    ... })
    ArgumentException:
'''


import re
import traceback
import copy
from woodstove import exceptions
from woodstove.common import logger
from woodstove.db import stormy


__sentinel__ = object()


class ArgumentList(object):
    '''
    Argument container

    @ivar args: C{dict} of argument specifications.
    @type args: C{dict}
    '''
    def __init__(self, arg_list=None):
        '''
        Setup the argument list by converting the L{arg_list} argument into a
        C{dict} keyed off the L{Argument.key} attribute.

        @keyword arg_list: List of L{Argument} objects that make up the list.
        '''
        self.args = dict()
        if arg_list:
            for arg in arg_list:
                self.args[arg.key] = arg

    def unknown(self, args):
        '''
        Check for arguments in the request that are not part of the argument
        list.

        @param args: The argument C{dict} passed in by the user.
        @raise ArgumentException: Raised if an unknown argument is found.
        '''
        if any(True for key in args if key not in self.args):
            raise exceptions.ArgumentException("Unknown argument in input")

    def validate(self, args, func=None, check_type=True):
        '''
        Verify that the L{args} C{dict} contains valid arguments based on
        this spec.

        @param args: The argument C{dict} passed in by the user.
        @keyword func: The function calling validate.
        @keyword check_type: Should the type of the passed in values be
            verified.
        @raise ArgumentException: Raised if any argument does not match spec.
        '''
        self.unknown(args)
        for arg in self.args.itervalues():
            arg.check(args, func, check_type)

        return args

    def update(self, mapping):
        '''
        Add the contents of L{mapping} to this argument list.

        @param mapping: C{dict} of arguments to add.
        '''
        self.args.update(mapping)

    def __deepcopy__(self, memo):
        '''
        Deep copy an ArugmentList object.

        @param memo: Memo dict used by deepcopy function.
        @return: New copy of this ArugmentList
        '''
        new = type(self)()
        new.args = copy.deepcopy(self.__dict__, memo)
        return new


class Argument(object):
    '''
    Argument specification

    @ivar key: Name of argument.
    @ivar type: Iterable of valid types (or ArgumentList object).
    @ivar optional: Is the argument optional?
    @ivar desc: Description of the argument.
    @ivar default: Default value if none is passed.
    @ivar hooks: Validation callback functions.
    @ivar required_funcs: Callers that should raise exceptions if required
        arguments are missing.
    @ivar censor: Should argument value be scrubbed from log output.
    '''

    def __init__(self, key, type, optional=False, desc=None,
                 default=__sentinel__, regex=None, disable_type_check=False,
                 censor=False):
        '''
        Setup argument instance.

        @param key: Name of argument
        @param type: Iterable of valid types (or ArgumentList object).
        @keyword optional: Is the argument optional?
        @keyword desc: Descpiption of the argument.
        @keyword default: Default value (implys L{optional})
        @keyword regex: Regular expression pattern.
        @keyword disable_type_check: disable the type check hook.
        @keyword censor: Should argument be censored in logs.
        '''
        self.hooks = dict()
        self.required_funcs = None
        self.private = dict()
        self.key = key
        self.type = type
        self.desc = desc
        self.default = default
        self.censor = censor

        if default is not __sentinel__ and not optional:
            optional = True

        self.optional = optional

        if isinstance(type, ArgumentList):
            self.hook(hook_recurse)
            return

        if not disable_type_check:
            self.hook(hook_type)

        if regex:
            self.hook(hook_regex, re.compile(regex))

    def hook(self, callback, private=None, funcs=None):
        '''
        Add a validation callback

        @param callback: function to add to callback set
        @keyword private: data to be used by the callback
        @return:
        '''
        self.hooks[callback] = {
            'private': private,
            'funcs': funcs,
        }
        return self

    def unhook(self, callback):
        '''
        Remove a validation callbac

        @param callback: function to remove from callback set
        '''
        del self.hooks[callback]

    def check(self, args, func=None, check_type=True):
        '''
        Check L{args} for valid value for this argument.

        @param args: The arguments passed by the user.
        @keyword func: Function calling validate.
        @keyword check_type: Should types be verified.
        @raise ArgumentException: If any validation hook fails.
        '''
        try:
            arg = args[self.key]
        except KeyError:
            try:
                if func not in self.required_funcs:
                    return args
            except TypeError:
                pass

            if self.optional:
                if self.default is not __sentinel__:
                    args[self.key] = self.default
                return args

            raise exceptions.ArgumentException('Missing required argument: %s'
                                               % self.key)

        for hook, opts in self.hooks.iteritems():
            larg = '*' * 10 if self.censor else arg
            logger.Logger(__name__).debug("Calling hook %r(%r, %r, %r, %r)" % (
                hook, self, larg, func, check_type))

            if opts['funcs'] and func not in opts['funcs']:
                continue

            try:
                opts['check_type'] = check_type
                args[self.key] = hook(self, arg, func, opts)
            except exceptions.ArgumentException:
                raise
            except Exception:
                logger.Logger(__name__).error("Exception in hook %r: %s" % (
                    hook, traceback.format_exc()))
                raise exceptions.ArgumentException(
                    "Error in argument validation")

        return args


class String(Argument):
    ''' String argument '''
    def __init__(self, key, **kwargs):
        '''
        @param key:
        @param **kwargs: Additional arguments passed to L{Argument}
            constructor.
        '''
        super(String, self).__init__(key, (unicode, str), **kwargs)


class Integer(Argument):
    ''' Integer Argument '''
    def __init__(self, key, **kwargs):
        '''
        @param key:
        @param **kwargs: Additional arguments passed to L{Argument}
            constructor.
        '''
        super(Integer, self).__init__(key, (int, long), **kwargs)


class Float(Argument):
    ''' Floating point Argument '''
    def __init__(self, key, **kwargs):
        '''
        @param key:
        @param **kwargs: Additional arguments passed to L{Argument}
            constructor.
        '''
        super(Float, self).__init__(key, (float,), **kwargs)


class Number(Argument):
    ''' Number argument '''
    def __init__(self, key, **kwargs):
        '''
        @param key:
        @param **kwargs: Additional arguments passed to L{Argument}
            constructor.
        '''
        super(Number, self).__init__(key, (int, long, float,), **kwargs)


class Bool(Argument):
    ''' Boolean Argument '''
    def __init__(self, key, **kwargs):
        '''
        @param key:
        @param **kwargs: Additional arguments passed to L{Argument}
            constructor.
        '''
        super(Bool, self).__init__(key, (bool, int), **kwargs)


class Storm(Argument):
    ''' Storm ORM class argument '''
    def __init__(self, key, klass, **kwargs):
        '''
        @param key:
        @param klass:
        @param **kwargs: Additional arguments passed to L{Argument}
            constructor.
        '''
        spec = storm_to_spec(klass)
        super(Storm, self).__init__(key, spec, **kwargs)


class Hook(Argument):
    ''' Hook callback argument '''
    def __init__(self, key, hook, private=None, **kwargs):
        '''
        Callback hook helper class.

        @param key: Argument name.
        @param hook: Callback function to be called when this argument is
            verified.
        @keyword private: Data to be stored in the argument for the hook.
        @param **kwargs: Additional arguments passed to L{Argument}
            constructor.
        '''
        super(Hook, self).__init__(key, None, **kwargs)
        self.hook(hook, private)

    def check(self, args, func=None, _=None):
        '''
        Overrides L{Argument.check} to force check_type to be set False.

        @param args: User argument C{dict}.
        @keyword func: Function calling validate.
        @raise ArgumentException: Raised if the callback raises an exception.
        '''
        return super(Hook, self).check(args, func, False)


class List(Argument):
    ''' List Argument '''
    def __init__(self, key, subtype=None, **kwargs):
        '''
        @param key:
        @keyword subtype: Type of values contained in the list.
        @param **kwargs: Additional arguments passed to L{Argument}
            constructor.
        '''
        super(List, self).__init__(key, (list, tuple), **kwargs)

        if subtype is not None:
            if isinstance(subtype, ArgumentList):
                self.hook(hook_seq_recurse, subtype)
            else:
                try:
                    _ = iter(subtype)
                    self.hook(hook_seq_type, subtype)
                except TypeError:
                    raise exceptions.InternalException('Invalid subtype: %r' %
                                                       subtype)


def storm_to_spec(obj, **kwargs):
    '''
    Create an ArgumentList object from a storm class

    @param obj: Storm class to use.
    '''
    type_map = {'Unicode': (str, unicode),
                'Int': (int, long),
                'DateTime': (str, unicode),
                'JSON': (str, unicode, int, long, list, dict),
                'Bool': (bool, int)}
    spec = ArgumentList()

    for name, column, property in stormy.inspect(obj):
        optional = True
        regex = None
        required_funcs = None
        regex_funcs = None

        try:
            if column._stove_hidden:
                continue
        except AttributeError:
            pass

        try:
            ktype = type_map[property.__class__.__name__]
        except KeyError:
            raise

        try:
            if property._stove_required:
                optional = False
            if property._stove_required_funcs:
                required_funcs = property._stove_required_funcs
        except AttributeError:
            pass

        try:
            regex = property._stove_regex

            try:
                regex_funcs = property._stove_regex_funcs
            except AttributeError:
                pass
        except AttributeError:
            pass

        arg = Argument(name, ktype, optional, desc='', regex=regex,
                       **kwargs)
        arg.required_funcs = required_funcs

        if regex:
            arg.hooks[hook_regex]['funcs'] = regex_funcs

        spec.args[name] = arg

    return spec


def hook_recurse(spec, arg, func, opts):
    '''

    @param spec:
    @param arg:
    @param func:
    @param opts:
    @return:
    @raise ArgumentException:
    '''
    return spec.type.validate(arg, opts['check_type'])


def hook_type(spec, arg, func, opts):
    '''
    Verify that the type of L{arg} is in the list of allowed types.

    @param spec:
    @param arg:
    @param func:
    @param opts:
    @return:
    @raise ArgumentException:
    '''
    if opts['check_type'] is False:
        return arg

    arg_type = type(arg)

    if arg_type not in spec.type:
        raise exceptions.ArgumentException("%s: %r is not %r" % (spec.key,
                                           arg_type, spec.type))

    return arg


def hook_regex(spec, arg, func, opts):
    '''
    Verify that L{arg} matches this arguments L{regex} pattern.

    @param spec:
    @param arg:
    @param func:
    @param opts:
    @return:
    @raise ArgumentException:
    '''
    arg = unicode(arg)
    pattern = opts['private']

    if re.search(pattern, arg) is None:
        raise exceptions.ArgumentException("%s: %r does not match regex %s" % (
                                           spec.key, arg, pattern))

    return arg


def hook_seq_type(spec, arg, func, opts):
    '''
    Check the type of all the values in an iterable.

    @param spec: Argument specification
    @param arg: User passed argument
    @param func: Function calling validate.
    @param opts: Options for the hook.
    @return: The processed argument.
    @raise ArgumentException: Raised if argument does not match pattern.
    '''
    types = opts['private']
    for val in arg:
        arg_type = type(val)
        if arg_type not in types:
            raise exceptions.ArgumentException("%s: %r is not %r" % (spec.key,
                                               arg_type, types))

    return arg


def hook_seq_recurse(spec, arg, func, opts):
    '''
    Check the type of all the values in an iterable.

    @param spec: Argument specification
    @param arg: User passed argument
    @param func: Function calling validate.
    @param opts: Options for the hook.
    @return: The processed argument.
    @raise ArgumentException: Raised if argument does not match pattern.
    '''
    spec = opts['private']

    for i in xrange(len(arg)):
        arg[i] = spec.validate(arg[i], opts['check_type'])

    return arg
