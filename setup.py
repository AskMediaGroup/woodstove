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
import sys
import glob
from distutils.core import setup

if sys.version_info < (2,6):
    raise NotImplementedError("Sorry, you need at least Python 2.6 to use woodstove.")

import woodstove 

setup(
    name='woodstove',
    version=woodstove.__version__,
    description='Framework for writing JSON HTTP APIs',
    long_description=woodstove.__doc__,
    author=woodstove.__author__,
    author_email=woodstove.__email__,
    url=woodstove.__url__,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
    ],
    packages=[
        'woodstove',
        'woodstove.app',
        'woodstove.async',
        'woodstove.auth',
        'woodstove.auth.adapters',
        'woodstove.common',
        'woodstove.db',
        'management',
        'management.debug',
        'management.job',
        'management.user',
    ],
    install_requires=[
        'bottle',
        'setproctitle',
        'storm',
        'rq',
        'twisted',
        'MySQL-python',
        'PyYAML',
    ],
    scripts=[
        'bin/woodstove-worker',
        'bin/woodstove-wsgi',
    ],
    data_files=[
        ('schema', glob.glob('schema/*.sql')),
        ('conf.d', glob.glob('conf.d/*.yml')),
    ],
)
