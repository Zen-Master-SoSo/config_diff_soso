# config_diff_soso

Copies the original configuration files and your changes with a diff.

## WHAT DID I DO!!!?

If you're like me, you make changes to your Debian/Ubuntu system as needed, and
don't always keep a good record of what you have done.

When I upgrade to a newer version of my operating system, I want to make the
same changes to the new install. That's what prompted me to create this script.

Now I can do a new installation with the newest package maintainer's version
of all the config files, and then go through the changed files and make the
fixes on the new install.

## Install

The usual pip installation:

```bash
$ pip install config_diff_soso
```

...or...

```bash
$ python3 -m pip install config_diff_soso
```

## Usage

```bash
$ config-diff-soso
```

## What it does

This script uses debsums to extract the package maintainer's config file for
every package on your system, and compares it to the version on your machine,
saving a copy of each with another file showing the differences between them.

It creates a directory in the current working directory with the following
template:

	<host name>-config-diff-<date>

Inside this directory will be created subdirectories which mirror the
directories and file name of each configuration file. The filename will be
stored as the final directory in the tree, with one file each for the original
package maintainer's version, your version, and a "diff" of the changes between
them.

For example, using "/etc/default/grub":

Original path:

    etc
    └── apache2
        └── apache2.conf

The differences will be saved as:

    etc
    └── apache2
        └── apache2.conf
            ├── diff
            ├── original
            └── yours

## Effects

This script makes no changes to your system, only records what you have already
changed.

It needs sudo rights to run some commands. Check the script before using it to
make sure it doesn't do anything malicious. I would. Run it as a regular user,
and you'll be prompted for your password when needed.

It takes a while for debsums to extract all the packages. Be patient. If you
upgrade a system with a lot of changes to system configuration files, it'll be
worth it.

The script downloads .deb files from your configured apt repository, if they do
not already exist. If you want to make sure that you download the most recent
versions, run "sudo apt-cache clean" before running this script.


