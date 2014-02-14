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
Defines a data structure for describing an asynchronous job.
'''

import uuid
import json
import time
import traceback
from storm.locals import Int, Unicode, JSON, Storm, Reference, Or, ReferenceSet
from woodstove import exceptions
from woodstove.common import logger, context
from woodstove.db import stormy


CREATED = 0
QUEUED = 1
RUNNING = 5
SUCCESS = 10
FAILED = 15
TIMEOUT = 20
FATAL = 25
STATE_MAP = {QUEUED: 'queued', RUNNING: 'running',
             SUCCESS: 'success', FAILED: 'failed',
             TIMEOUT: 'timeout', FATAL: 'fatal'}


class Job(Storm):  # pylint: disable=R0902
    ''' Storm object representing job table '''
    __storm_table__ = 'woodstove_job'
    uuid = Unicode(primary=True)
    parent_uuid = Unicode()
    state = Int()
    output = JSON()
    queue_time = Int()
    start_time = Int()
    end_time = Int()
    user_id = Int()
    path = Unicode()
    module = Unicode()
    func = Unicode()
    args = Unicode()
    kwargs = Unicode()
    user = Reference(user_id, "User.user_id")
    parent = Reference(parent_uuid, "Job.uuid")
    children = ReferenceSet("Job.uuid", "Job.parent_uuid")
    cleanup_handlers = None
    cleanup_list = None

    def __init__(self, func=None, args=None, kwargs=None, parent=None):
        ''' Setup new job with both stateful database information and stateless
            run time information. '''
        super(Job, self).__init__()
        self.state = 0
        self.func = unicode(func.__name__)
        self.module = unicode(func.__module__)
        self.args = unicode(json.dumps(args)) if args else u'[]'
        self.kwargs = unicode(json.dumps(kwargs)) if kwargs else u'{}'
        self.uuid = unicode(uuid.uuid4())
        if parent:
            self.parent_uuid = parent.uuid
        self.init()

    def init(self):
        ''' Setup non storm things '''
        self.cleanup_handlers = list()

    def register_cleanup_handler(self, func, args=None, kwargs=None, key=None):
        ''' Setup a cleanup handler '''
        ckey = '__all__'
        if key:
            ckey = key
        else:
            for ctx in context.ctx_get():
                try:
                    ckey = ctx['job_cleanup_key']
                    break
                except KeyError:
                    pass

        if not args:
            args = ()
        if not kwargs:
            kwargs = {}

        self.cleanup_handlers.insert(0, (ckey, func, args, kwargs))

    def delete_cleanup_handlers(self, key):
        ''' Remove all handlers that match key '''
        self.cleanup_handlers = [x for x
                                 in self.cleanup_handlers
                                 if x[0] != key]

    def call_cleanup_handlers(self):
        ''' Call all registered cleanup handlers '''
        logger.Logger(__name__).debug("Calling cleanup handlers for job: %s" %
                                      self.uuid)
        for handler in self.cleanup_handlers:
            try:
                msg = "Calling cleanup handler %r(%r, %r)" % (handler[1],
                                                              handler[2],
                                                              handler[3])
                logger.Logger(__name__).debug(msg)
                handler[1](*handler[2], **handler[3])
            except Exception:  # pylint: disable=W0703
                logger.Logger(__name__).debug(traceback.format_exc())

    def queued(self):
        ''' Set job to queued '''
        self.state = QUEUED
        self.queue_time = int(time.time())
        stormy.Stormy().commit()

    def running(self):
        ''' Set job to running '''
        self.state = RUNNING
        self.start_time = int(time.time())
        stormy.Stormy().commit()

    def end(self, state):
        ''' End the job '''
        self.state = SUCCESS
        self.end_time = int(time.time())
        stormy.Stormy().commit()

    def success(self):
        ''' set job to success '''
        self.end(SUCCESS)

    def failed(self, cleanup=True):
        ''' set job to failed '''
        if cleanup:
            self.call_cleanup_handlers()
        self.end(FAILED)

    def timeout(self, cleanup=True):
        ''' set job to timeout '''
        if cleanup:
            self.call_cleanup_handlers()
        self.end(TIMEOUT)

    def fatal(self):
        ''' set job to fatal '''
        self.end(FATAL)

    @classmethod
    def fail(cls, msg=None):
        ''' Fail job '''
        raise exceptions.JobException(msg)


def fail_all():
    ''' Fail all QUEUED/RUNNING jobs '''
    store = stormy.Stormy()
    jobs = store.find(Job, Or(Job.state == RUNNING, Job.state == QUEUED))
    for job in jobs:
        logger.Logger(__name__).debug("Failing job: %r" % job)
        job.state = FAILED
    store.commit()


def delete_old():
    ''' Delete jobs older than 24 hours '''
    store = stormy.Stormy()
    jobs = store.find(Job, Job.queue_time < int(time.time()) - (3600 * 24))
    for job in jobs:
        logger.Logger(__name__).debug("Removing job: %r" % job)
        store.remove(job)
    store.commit()


class CleanupContext(context.Context):
    ''' '''
    def __init__(self, key, job):
        ''' '''
        self.job = job
        self.key = key
        super(CleanupContext, self).__init__(job_cleanup_key=key)

    def __exit__(self, *args, **kwargs):
        ''' '''
        if not args[0]:
            self.job.delete_cleanup_handlers(self.key)
        super(CleanupContext, self).__exit__(*args, **kwargs)
