#!/usr/bin/env python
#
# Copyright 2013 Richard Goodwin (some parts borrowed from Major Hayden's
# supernova")
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
import ConfigParser
import glanceclient
import keyring
import keystoneclient.v2_0.client as ksclient
import logging
import os
import re
import subprocess
import sys

LOG = logging.getLogger(__name__)

__version__ = '0.7.5'


class SuperGlance:

    def __init__(self):
        self.glance_creds = None
        self.glance_env = None
        self.keystone_creds = None
        self.image_url = None
        self.env = os.environ.copy()

    def check_deprecated_options(self):
        """
        Hunts for deprecated configuration options from previous Superglance
        versions.
        """
        creds = self.get_glance_creds()
        if creds.has_option(self.glance_env, 'insecure'):
            msg = "WARNING: the 'insecure' option is deprecated. " \
                "Consider using GLANCECLIENT_INSECURE=1 instead."
            print msg
            LOG.warning(msg)

    def get_glance_creds(self):
        """
        Reads the superglance config file from the current directory or the
        user's home directory.  If the config file has already been read, the
        cached copy is immediately returned.
        """
        if self.glance_creds:
            return self.glance_creds

        possible_configs = [os.path.expanduser("~/.superglance"),
                            '.superglance']
        self.glance_creds = ConfigParser.RawConfigParser()
        self.glance_creds.read(possible_configs)
        if len(self.glance_creds.sections()) < 1:
            return None
        return self.glance_creds

    def is_valid_environment(self):
        """
        Checks to see if the configuration file contains a section for our
        requested environment.
        """
        valid_envs = self.get_glance_creds().sections()
        return self.glance_env in valid_envs

    def password_get(self, username=None):
        """
        Retrieves a password from the keychain based on the environment and
        configuration parameter pair.
        """
        try:
            return keyring.get_password('superglance', username)
        except:
            return False

    def password_set(self, username=None, password=None):
        """
        Stores a password in a keychain for a particular environment and
        configuration parameter pair.
        """
        try:
            keyring.set_password('superglance', username, password)
            return True
        except:
            return False

    def prep_glance_creds(self):
        """
        Finds relevant config options in the superglance config and cleans them
        up for glanceclient.
        """
        self.check_deprecated_options()
        raw_creds = self.get_glance_creds().items(self.glance_env)
        glance_re = re.compile(r"(^glance_|^os_|^glanceclient)")

        creds = []
        for param, value in raw_creds:

            # Skip parameters we're unfamiliar with
            if not glance_re.match(param):
                continue

            param = param.upper()

            # Get values from the keyring if we find a USE_KEYRING constant
            if value.startswith("USE_KEYRING"):
                if value == "USE_KEYRING":
                    username = "%s:%s" % (self.glance_env, param)
                else:
                    global_identifier = re.match(
                        "USE_KEYRING\['(.*)'\]", value).group(1)
                    username = "%s:%s" % ('global', global_identifier)
                credential = self.password_get(username)
            else:
                credential = value.strip("\"'")

            # Make sure we got something valid from the configuration file or
            # the keyring
            if not credential:
                msg = "Attempted to retrieve a credential for %s but " \
                      "couldn't find it within the keyring." % username
                LOG.error(msg)
                raise Exception(msg)

            creds.append((param, credential))

        return creds

    def prep_shell_environment(self):
        """
        Appends new variables to the current shell environment temporarily.
        """
        for k, v in self.prep_glance_creds():
            self.env[k] = v

    def run_glanceclient(self, glance_args, force_debug=False):
        """
        Sets the environment variables for glanceclient, runs glanceclient, and
        prints the output.
        """
        # Get the environment variables ready
        self.prep_shell_environment()

        # Check for a debug override
        if force_debug:
            glance_args.insert(0, '--debug')

        # Call glanceclient and connect stdout/stderr to the current terminal
        # so that any unicode characters from glanceclient's list will be
        # displayed appropriately.
        #
        # In other news, I hate how python 2.6 does unicode.
        if glance_args[0] != '-k':
            glance_args.insert(0, '-k')
        LOG.info('Running glance client in env %r with args %r',
                 self.glance_env, glance_args)
        print '-- %s --' % self.glance_env
        p = subprocess.Popen(['glance'] + glance_args,
                             stdout=subprocess.PIPE,
                             stderr=sys.stderr,
                             env=self.env
                             )
        for line in p.stdout:
            sys.stdout.write(line)
            LOG.info(line)

        # Don't exit until we're sure the subprocess has exited
        p.wait()

    def get_glanceclient(self, env):
        """
        Returns python glanceclient object authenticated with superglance cfg.
        """
        self.glance_env = env
        assert self.is_valid_environment(), "Env %s not found in config." % env
        self.prep_keystone_creds()
        return glanceclient.Client(
            self.keystone_creds.pop('version', '1'),
            self.image_url,
            token=ksclient.Client(**self.keystone_creds).auth_token
        )

    def prep_keystone_creds(self):
        """
        Prepare credentials for python Client instantiation.
        """
        creds = {rm_prefix(k[0]): k[1] for k in self.prep_glance_creds()}
        if creds.get('image_url'):
            self.image_url = creds.pop('image_url')
        self.keystone_creds = creds


def rm_prefix(name):
    """
    Removes NOVA_ OS_ NOVACLIENT_ prefix from string and lowercases.
    """
    names = name.split('_')
    for prefix in ['NOVA', 'GLANCECLIENT', 'OS']:
        if names[0].upper() == prefix:
            del names[0]
            return "_".join(names).lower()
    return name.lower()
