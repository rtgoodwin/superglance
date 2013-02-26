#!/usr/bin/env python
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
import getpass
import optparse
import superglance
import sys


def gwrap(some_string):
    """
    Returns green text
    """
    return "\033[92m%s\033[0m" % some_string


def rwrap(some_string):
    """
    Returns red text
    """
    return "\033[91m%s\033[0m" % some_string


def print_valid_envs(valid_envs):
    """
    Prints the available environments.
    """
    print "[%s] Your valid environments are:" % (gwrap('Found environments'))
    print "%r" % valid_envs


def run_superglance():
    """
    Handles all of the prep work and error checking for the
    superglance executable.
    """
    s = superglance.SuperGlance()
    parser = optparse.OptionParser()
    parser.add_option('-d', '--debug', action="store_true",
            dest="debug", default=False,
            help='show glanceclient debug output')
    parser.add_option('-l', '--list', action="store_true",
            dest="listenvs", default=False,
            help='list all configured environments')

    # Allow for passing --options all the way through to glanceclient
    parser.disable_interspersed_args()
    (opts, args) = parser.parse_args()

    # Is the config file missing or empty?
    if s.get_glance_creds() == None:
        print "[%s] Unable to find your superglance configuration file or " \
              "your configuration file is malformed." % (
                    rwrap("Configuration missing"))
        sys.exit()

    # Should we just list the available environments and exit?
    if opts.listenvs:
        for glance_env in s.get_glance_creds().sections():
            envheader = "-- %s " % gwrap(glance_env)
            print envheader.ljust(86, '-')
            for param, value in sorted(s.get_glance_creds().items(glance_env)):
                print "  %s: %s" % (param.upper().ljust(21), value)
        sys.exit()

    # Did we get a valid environment?
    try:
        s.glance_env = args[0]
        if not s.is_valid_environment():
            print "[%s] Unable to find the %r environment in your " \
                  "configuration file.\n" % (
                    rwrap('Invalid environment'), args[0])
            print_valid_envs(sorted(s.get_glance_creds().sections()))
            sys.exit()
    except IndexError:
        print "[%s] A valid glance environment is required as the first " \
              "argument.\n" % (rwrap("Environment missing"))
        print_valid_envs(sorted(s.get_glance_creds().sections()))
        sys.exit()

    # Did we get any arguments to pass on to glance?
    if len(args) <= 1:
        print "[%s] No arguments were provided to pass along to glance." % (
            rwrap('Missing glanceclient arguments'))
        sys.exit()

    # All of the remaining arguments should be handed off to glance
    glanceclient_args = args[1:]
    s.run_glanceclient(glanceclient_args, opts.debug)


def run_superglance_keyring():
    """
    Handles all of the prep work and error checking for the
    superglance-keyring executable.
    """
    s = superglance.SuperGlance()
    parser = optparse.OptionParser()
    parser.add_option('-g', '--get', action="store_true",
            dest="get_password", default=False,
            help='retrieves credentials from keychain storage')
    parser.add_option('-s', '--set', action="store_true",
            dest="set_password", default=False,
            help='stores credentials in keychain storage')
    (opts, args) = parser.parse_args()

    if opts.get_password and opts.set_password:
        print "[%s] You asked to get and set a password at the same time. " \
              "This is not supported." % rwrap("Too many options")

    # No matter what, we need two arguments: environment and a
    # configuration option
    if len(args) != 2:
        print "[%s] Usage: superglance-keyring [--get | --set] " \
              "environment parameter" % rwrap("Invalid number of arguments")
        sys.exit()

    username = "%s:%s" % (args[0], args[1])

    if opts.set_password:
        print "[%s] Preparing to set a password in the keyring for:" % (
            gwrap("Keyring operation"))
        print "  - Environment  : %s" % args[0]
        print "  - Parameter    : %s" % args[1]
        print "\n  If this is correct, enter the corresponding credential " \
              "to store in \n  your keyring or press CTRL-D to abort: ",

        # Prompt for a password and catch a CTRL-D
        try:
            password = getpass.getpass('')
        except:
            password = None
            print

        # Did we get a password from the prompt?
        if not password or len(password) < 1:
            print "\n[%s] No data was altered in your keyring." % (
                rwrap("Canceled"))
            sys.exit()

        # Try to store the password
        try:
            store_ok = s.password_set(username, password)
        except:
            store_ok = False

        if store_ok:
            print "\n[%s] Successfully stored credentials for %s under the " \
                  "superglance service." % (gwrap("Success"), username)
        else:
            print "\n[%s] Unable to store credentials for %s under the " \
                  "superglance service." % rwrap("Failed", username)

        sys.exit()

    if opts.get_password:
        print "[%s] If this operation is successful, the credential " \
              "stored \nfor %s will be displayed in your terminal as " \
              "plain text." % (rwrap("Warning"), username)
        print "\nIf you really want to proceed, type yes and press enter:",
        confirm = raw_input('')

        if confirm != 'yes':
            print "\n[%s] Your keyring was not read or altered." % (
                rwrap("Canceled"))
            sys.exit()

        try:
            password = s.password_get(username)
        except:
            password = None

        if password:
            print "\n[%s] Found credentials for %s: %s" % (
                gwrap("Success"), username, password)
        else:
            print "\n[%s] Unable to retrieve credentials for %s.\nThere are " \
                  "probably no credentials stored for this environment/" \
                  "parameter combination (try --set)." % (
                    rwrap("Failed"), username)
