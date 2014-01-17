superglance
===========

A helpful utility, similar to supernova, for working with OpenStack Glance deployments.
Shamelessly and gratefully borrowed in large part from Major Hayden's *supernova*:
http://rackerhacker.github.com/supernova/


## superglance - use glanceclient with multiple glance environments the easy way

You may like *superglance* if you regularly have the following problems:

* You have 10 open "scratch files" or TextExpanders with glance commands to keep straight
* You get your terminals confused and do the wrong things in the wrong glance environment
* You don't like remembering things
* You want to keep sensitive API keys and passwords out of plain text configuration files (see the "Working with keyrings" section toward the end)
* You need to share common skeleton environment variables for *glance* with your teams
* You were already a fan of *supernova* on which I HEAVILY based this :)

Questions, comments, and pull requests welcome; here, or richard.goodwin@rackspace.com


### Installation

    Install git if not already

    Ubuntu:
    apt-get install python-dev
    apt-get install libffi-dev
    apt-get install libssl-dev
    apt-get install python-pip

    git clone git@github.com:rtgoodwin/superglance.git
    cd superglance
    python setup.py install

### Configuration

For *superglance* to work properly, each environment must be defined in `~/.superglance` (in your user's home directory).  The data in the file is exactly the same as the environment variables which you would normally use when running *glance*.  You can copy/paste from your glancerc files directly into configuration sections within `~/.superglance`.

Here's an example of two environments, **production** and **development**:

    [production]
    OS_AUTH_URL=https://123.123.123.123:5000/v2.0
    OS_USERNAME= my_username
    OS_PASSWORD = my_pass
    OS_TENANT_ID = glance-production
    OS_IMAGE_URL = https://123.123.123.123:9292/v1
    #GLANCECLIENT_INSECURE = 1 (if not using proper SSL)
    #INSECURE = 1

    [development]
    OS_AUTH_URL=https://223.223.223.223:5000/v2.0
    OS_USERNAME= my_username
    OS_PASSWORD = my_pass
    OS_TENANT_ID = glance-production
    OS_IMAGE_URL = https://223.223.223.223:9292/v1

    When you use *superglance*, you'll refer to these environments as **production** and **development**.  Every environment is specified by its configuration header name.

### Configuration Groups

Configuration groups allow you to run the same command across multiple environments.  This is defined in your `.superglance` config file as well.

Here's an example of how you would define an [all] group for the above example:

    [all]
    GROUP=['production', 'development']

### Usage

    superglance [--debug] [--list] [environment] [glanceclient arguments...]

    Options:
    -h, --help   show this help message and exit
    -d, --debug  show glanceclient debug output (overrides NOVACLIENT_DEBUG)
    -l, --list   list all configured environments

##### Passing commands to *glance*

For example, if you wanted to list all images within the **production** environment:

    superglance production image-list

Show a particular instance's data in the preprod environment:

    superglance preprod image-show 3edb6dac-5a75-486a-be1b-3b15fd5b4ab0a

The first argument is generally the environment argument and it is expected to be a single word without spaces. Any text after the environment argument is passed directly to *glance*.

##### Debug override

You may optionally pass `--debug` as the first argument (before the environment argument) to inject the `glanceCLIENT_DEBUG=1` option into the process environment to see additional debug information about the requests being made to the API:

    superglance --debug production list

As before, any text after the environment argument is passed directly to *glance*.

##### Logging

File logging is enabled by default and will save a `superglance.log` file to the current directory.  Logging can be configured by defining a `[log]` section in your `.superglance` config file with level, handler and filename(path) as config options.

Here's an example of specifying an alternative file location and log level:

    [log]
    handler=FileHandler
    level=debug
    filename=log/superglance.log

Setting the handler to **NullHandler** will disable logging as well.

##### Listing your configured environments

You can list all of your configured environments by using the `--list` argument.

### Working with keyrings
Due to security policies at certain companies or due to general paranoia, some users may not want API keys or passwords stored in a plaintext *superglance* configuration file.  Luckily, support is now available (via the [keyring](http://pypi.python.org/pypi/keyring) module) for storing any configuration value within your operating system's keychain.  This has been tested on the following platforms:

* Mac: Keychain Access.app
* Linux: gnome-keyring, kwallet

To get started, you'll need to choose an environment and a configuration option.  Here's an example of some data you might not want to keep in plain text:

    superglance-keyring --set production glance_API_KEY

**TIP**: If you need to use the same data for multiple environments, you can use a global credential item very easily:

    superglance-keyring --set global MyCompanyLDAPPassword

Once it's stored, you can test a retrieval:

    # Normal, per-environment storage
    superglance-keyring --get production glance_API_KEY

    # Global storage
    superglance-keyring --get global MyCompanyLDAPPassword

You'll need to confirm that you want the data from your keychain displayed in plain text (to hopefully thwart shoulder surfers).

Once you've stored your sensitive data, simply adjust your *superglance* configuration file:

    #glance_API_KEY = really_sensitive_api_key_here

    # If using storage per environment
    glance_API_KEY = USE_KEYRING

    # If using global storage
    glance_API_KEY = USE_KEYRING['MyCompanyLDAPPassword']

When *superglance* reads your configuration file and spots a value of `USE_KEYRING`, it will look for credentials stored under `glance_API_KEY` for that environment automatically.  If your keyring doesn't have a corresponding credential, you'll get an exception.

#### A brief note about environment variables

*superglance* will only replace and/or append environment variables to the already present variables for the duration of the *glance* execution. If you have `glance_USERNAME` set outside the script, it won't be used in the script since the script will pull data from `~/.superglance` and use it to run *glance*. In addition, any variables which are set prior to running *superglance* will be left unaltered when the script exits.

#### Python Integration

Superglance can also be used to return a python-glanceclient object.  This can allow superglance to manage your credentials for multi-env python apps etc.

Here's an example of retrieving a image object for the [production] environment from above:

    import superglance.superglance as superglance
    glance_obj = superglance.SuperGlance().get_glanceclient('production')
    image = glance_obj.images.get('aaaaaaaa-bbbb-abab-cccc-dddddddd')

Happy hacking!
