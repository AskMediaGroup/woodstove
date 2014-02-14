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
''' App Class '''

import sys
import inspect
import bottle
import functools
import collections
from woodstove import app, exceptions, plugin
from woodstove.app import arguments, exhandlers
from woodstove.auth import user, adapter
from woodstove.async import dispatcher
from woodstove.common import logger, context
from woodstove.db import stormy


# pylint: disable=C0103
RouteSpec = collections.namedtuple('RouteSpec',
                                   ['path', 'verb', 'kwargs', 'private'])


def path(path, auto=True, **kwargs):
    '''
    Class decorator to setup where this app should get mounted

    @keyword auto: Add app to app list automatically
    @keyword **kwargs: Arugments to pass
    '''
    def decorator(cls):
        '''
        Decorator!!!

        @param cls: App class to configure.
        @return: The configured App class.
        '''
        module_name = inspect.getmodule(cls).__name__.split('.')[0]
        module = sys.modules[module_name]
        cls.path = path
        cls.app_args = kwargs

        try:
            cls.namespace = module.NAMESPACE
        except AttributeError:
            cls.namespace = '/' + module_name

        if auto:
            app.add_app(cls)

        return cls

    return decorator


def _call_route_setup_hooks(func, spec, kwargs):
    '''

    @param func:
    @param spec:
    @param kwargs:
    '''
    plugin.call_hooks('route', 'setup', func, spec, kwargs)


def _call_route_enter_hooks(func, args, kwargs):
    '''

    @param func:
    @param spec:
    @param kwargs:
    '''
    plugin.call_hooks('route', 'enter', func, args, kwargs)


def _call_route_exit_hooks(func, args, kwargs, ret):
    '''

    @param func:
    @param spec:
    @param kwargs:
    @param ret:
    '''
    plugin.call_hooks('route', 'exit', func, args, kwargs, ret)


def _call_route_exception_hooks(func, args, kwargs, ret):
    '''

    @param func:
    @param spec:
    @param kwargs:
    @param ret:
    '''
    plugin.call_hooks('route', 'exception', func, args, kwargs, ret)


def _call_route_context_hooks(func, args, kwargs, ctx, request):
    '''

    @param func:
    @param spec:
    @param kwargs:
    @param ctx:
    @param request:
    '''
    plugin.call_hooks('route', 'context', func, args, kwargs, ctx, request)


def route(method, path, **kwargs):  # pylint: disable=R0912
    '''
    Decorator to setup url path to function routing

    @param method: HTTP verb.
    @param path: URL path spec.
    @param **kwargs: Additional arguments that router hooks may need.
    @return: Returns decorator function.
    '''
    def decorator(func):
        '''
        Route Decorator!!!

        @param func: App method being wrapped.
        @return: New function wrapping L{func}.
        '''
        spec = RouteSpec(path, method, kwargs, {})
        func.route = spec

        _call_route_setup_hooks(func, spec, kwargs)

        @functools.wraps(func)
        def closure(*args, **kwargs):
            '''
            Call the wrapped route and handle exceptions

            @param *args: Positional arguments for L{func}.
            @param **kwargs: Keyword arguments for L{func}.
            @return: API response object.
            '''
            ctx = {}
            _call_route_context_hooks(func, args, kwargs, ctx, bottle.request)

            with context.Context(**ctx):
                logger.Logger(__name__).debug("Calling: %s(%r, %r)" % (
                                              func.__name__, args, kwargs))
                ret = None
                _call_route_enter_hooks(func, args, kwargs)

                try:
                    # If we get here with a pending transaction we don't want
                    # to keep it so doing a rollback here. A side effect of
                    # this is that if we've lost the database connection the
                    # rollback call will trigger a reconnect.
                    stormy.Stormy().rollback()

                    try:
                        ret = func(*args, **kwargs)
                    except BaseException as execp:
                        _call_route_exception_hooks(func, args, kwargs, execp)
                        raise

                    _call_route_exit_hooks(func, args, kwargs, ret)
                except Exception as execp:
                    ret = exhandlers.run_exc_handler(execp, func)

                return ret

        return closure

    return decorator


def get(path, **kwargs):
    ''' get => route(method='GET') '''
    return route('GET', path, **kwargs)


def post(path, **kwargs):
    ''' post => route(method='POST') '''
    return route('POST', path, **kwargs)


def put(path, **kwargs):
    ''' put => route(method='PUT') '''
    return route('PUT', path, **kwargs)


def delete(path, **kwargs):
    ''' delete => route(method='DELETE') '''
    return route('DELETE', path, **kwargs)


class App(object):
    '''
    App class

    @var path:
    @var namespace:
    '''

    path = None
    namespace = None

    def __init__(self, path=None, namespace=None):
        '''

        @keyword path: Path for this app in the namespace.
        @keyword namespace: Namespace to place app in.
        '''
        if path:
            self.path = path
        if namespace:
            self.namespace = namespace

    def mount(self, bapp=None):
        '''
        Mount app.

        @keyword bapp: Parent bottle app.
        '''
        if not bapp:
            bapp = bottle.Bottle()

        for name, attr in inspect.getmembers(self):
            try:
                bapp.route(attr.route.path, attr.route.verb, callback=attr)
            except AttributeError:
                if isinstance(attr, App):
                    attr.mount(bapp)

        try:
            for key, arglist in self.argfmt.iteritems():
                if not isinstance(arglist, arguments.ArgumentList):
                    self.argfmt[key] = arguments.storm_to_spec(arglist)
        except AttributeError:
            pass

        return bapp

    @classmethod
    def response(cls, *args, **kwargs):
        '''
        API Response

        @return: Formated api response object.
        '''
        return app.response(*args, **kwargs)

    @classmethod
    def body(cls):
        '''
        Get HTTP body json object

        @return: Request body dict.
        '''
        body = bottle.request.json
        return body if body else dict()

    @classmethod
    def query(cls):
        '''
        Get HTTP query dict

        @return: Request query dict.
        '''
        return bottle.request.query

    @classmethod
    def wsgi_response(cls):
        '''
        Get WSGI Response object

        @return: Bottle response instance.
        '''
        return bottle.response

    @classmethod
    def wsgi_request(cls):
        '''
        Get WSGI Request object

        @return: Bottle request instance.
        '''
        return bottle.request

    def auth(self, acl=None, **opts):
        '''
        Perform authentication and optionally access control.

        @keyword acl: Optional ACL to verify.
        @raise AuthException: Raised if request is not able to be
            authenticated.
        '''
        auth_adapter = adapter.AuthAdapter()
        user_obj = self.get_user()
        auth_adapter.login(user_obj, self.get_creds())

        if acl:
            self.acl(acl, user_obj, opts)

    def acl(self, acl, user_obj=None, opts=None):
        '''
        Convinience helper to verify and ACL object against the current
        request.

        @param acl: ACL to verify.
        @keyword user_obj: User object to verify with.
        @raise AuthException: Raised if request is not able to be
            verified.
        '''
        if user_obj is None:
            user_obj = self.get_user()

        acl.verify(user_obj, self.wsgi_request(), opts)

    def get_creds(self):
        '''
        '''
        auth_adapter = adapter.AuthAdapter()
        return auth_adapter.request()

    def get_user(self):
        '''
        '''
        creds = self.get_creds()
        user_obj = stormy.Stormy().find(user.User, name=creds.name).one()

        if user_obj is None:
            raise exceptions.AuthException("bad user")

        if not user_obj.active:
            raise exceptions.AuthException("Inactive user")

        return user_obj

    @classmethod
    def set_status(cls, code):
        '''
        Set http response code

        @param code: New HTTP response code.
        '''
        bottle.response.status = code

    def async(self, func, args=None, kwargs=None):
        '''
        Put async call onto queue

        @param func:
        @keyword args:
        @keyword kwargs:
        @return:
        '''
        user_obj = None
        self.set_status(202)
        username = self.get_creds().name

        if username:
            user_obj = user.get_user()

        self.set_status(202)
        return dispatcher.add_job(func, args, kwargs, user=user_obj)

    def validate(self, expected, actual=None, chktype=True, logging=True,
                 func=None):
        '''
        Validate input arguments.

        @param expected:
        @keyword actual:
        @keyword chktype:
        @keyword logging:
        @keyword func:
        @return:
        @raise ArugmentException:
        '''
        if actual is None:
            actual = self.body()

        return expected.validate(actual, func, chktype)
