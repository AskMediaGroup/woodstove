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
Woodstove worker
'''

import traceback
import sys
import json
import rq
import rq.timeouts
import redis
from woodstove.db import stormy
from woodstove.async import job
from woodstove.common import logger, config, context
from woodstove import exceptions, server, plugin


def worker_exception_handler(job, exc_type, exc_value, trace):
    '''
    Handle exceptions in worker.

    @param job:
    @param exc_type:
    @param exc_value:
    @param trace:
    '''
    try:
        uuid = job.args[0]
        logger.Logger(__name__).error("Starting exception handling for job: %s"
                                      % uuid)
        conf = config.Config().woodstove.queue
        job_obj = stormy.generic_get(job.Job, uuid)

        with context.Context(job=job_obj):
            try:
                logger.Logger(__name__).error("Error in job (%s): %s" % (
                                              job.uuid, str(exc_value)))

                with rq.timeouts.death_penalty_after(
                        conf.cleanup_timeout * len(job.cleanup_handlers)):
                    if exc_type == rq.timeouts.JobTimeoutException:
                        job.timeout()

                    if isinstance(exc_type, exceptions.BaseWoodstoveException):
                        job.failed()
                    else:
                        tracestr = "".join(traceback.format_exception(exc_type,
                                           exc_value, trace))
                        logger.Logger(__name__).debug("Unhandled exception: %s"
                                                      % tracestr)
                        job.failed()
            except rq.timeouts.JobTimeoutException:
                job.fatal()
    except Exception:
        logger.Logger(__name__).error(traceback.format_exc())
    finally:
        stormy.Stormy().close()


def start_worker():
    ''' start woodstove worker '''
    server.load_config()
    conf = config.Config().woodstove.queue
    argv = sys.argv[1:]

    if not argv:
        argv = [conf.std_name, conf.bulk_name]

    with rq.Connection(redis.Redis(conf.host, conf.port)):
        qs = [rq.Queue(x) for x in argv]
        w = rq.Worker(qs, exc_handler=worker_exception_handler)
        w.work()


def run_job(uuid):
    '''

    @param uuid: UUID of job to run.
    '''
    config.load_config()
    server.setup_logging()
    plugin.load_plugins()
    server.import_apps(config.Config().woodstove.apps, False)

    try:
        job_obj = stormy.generic_get(job.Job, uuid)
    except exceptions.NotFoundException:
        logger.Logger(__name__).warning("Received bad job from queue: %s!" %
                                        uuid)
        return

    with context.Context(job=job_obj):
        logger.Logger(__name__).debug('Handling job: %s' % uuid)
        job.init()

        if job.state != job.QUEUED:
            logger.Logger(__name__).error("Got job with state %d expected %d" %
                                          (job.state, job.QUEUED))
            job.fatal()
            return

        mod = sys.modules[job.module]
        func = getattr(mod, job.func)
        job.running()
        logger.Logger(__name__).debug("Calling %s(*%r, **%r)", job.func,
                                      job.args, job.kwargs)
        func(*json.loads(job.args), job=job, **json.loads(job.kwargs))
        job.success()
        stormy.Stormy().close()
