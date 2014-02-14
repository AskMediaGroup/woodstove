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
Asynchronous work consumer
'''

import traceback
from redis import Redis
from rq import Connection, Queue

from woodstove.async import job, worker
from woodstove.common import logger, config
from woodstove.db import stormy


def add_job(func, args=None, kwargs=None, parent=None, user=None,
            timeout=None, bulk=False):
    ''' Add a job '''
    conf = config.Config().woodstove.queue
    store = stormy.Stormy()
    task = job.Job(func, args, kwargs, parent=parent)

    if user:
        task.user_id = user.user_id

    if timeout and timeout > conf.std_timeout:
        bulk = True

    if bulk:
        qname = conf.bulk_queue

        if not timeout:
            timeout = conf.bulk_timeout
    else:
        qname = conf.std_queue
        if not timeout:
            timeout = conf.std_timeout

    store.add(task)
    store.commit()

    try:
        with Connection(Redis(conf.host, conf.port)):
            queue = Queue(qname)
            logger.Logger(__name__).info("Queueing job %s" % task.uuid)
            task.queued()
            queue.enqueue_call(func=worker.run_job, args=(task.uuid,),
                               result_ttl=500, timeout=timeout)
    except Exception:
        logger.Logger(__name__).debug(traceback.format_exc())
        logger.Logger(__name__).error("Error enqueueing job %s" % task.uuid)
        task.failed()

    return task
