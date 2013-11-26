#!/usr/bin/python
#
# Copyright 2013 Richard Goodwin (some parts borrowed from Major Hayden's "supernova")
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
from setuptools import setup


setup(
    name='superglance',
    version='0.7.5',
    author='Richard Goodwin (but mostly Major Hayden)',
    author_email='richard.goodwin@rackspace.com',
    description="glanceclient wrapper for multiple glance environments",
    install_requires=['six>=1.4.1', 'keyring', 'simplejson', 'pycrypto', 'python-glanceclient'],
    packages=['superglance'],
    url='https://github.com/rtgoodwin/superglance',
    entry_points={
        'console_scripts': [
            'superglance = superglance.executable:run_superglance',
            'superglance-keyring = superglance.executable:run_superglance_keyring'],
        }
    )
