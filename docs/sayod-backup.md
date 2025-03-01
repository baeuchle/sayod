# sayod-backup

``sayod-backup`` is the main entrypoint for sayod.

## Command line usage

```bash
$ sayod-backup --help
usage: sayod-backup [-h] [--version] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                    --config CONFIGURATION_FILE [--notify | --no-notify] [--force]
                    {config,notify,logreader,receive,remotereader,squasher,analyse,
                     copy,database,grandcommit,replace-git,smallcommit,zipped-git}
...
```

Most command line options apply to all commands and must be given before
the command name. Most configuration must be set in
[CONFIGURATION_FILE](docs/configuration_file)

> **--force**, **-f**
>> Force the action even if during its [deadtime](docs/context).
>
> **--log-level** {DEBUG,INFO,WARNING,ERROR,CRITICAL}
>> Set logging level. Note that logging to systemd's journal is always on
>> level DEBUG; this option controls direct output of the program.
>
> **--notify**, **--no-notify**
>> Show or suppress status notifications on screen. Notifications are
>> meant to give some visual feedback, especially for error messages, to
>> a user.  In server environments, there will usually be no user using
>> a graphical interface at any time, so that ``--no-notify`` will be of
>> use there.
>>
>> See also [the page about notification](docs/notification)
>
> **--config** CONFIGURATION_FILE
>> Specifies the configuration file. If the filename is not absolute, it
>> will be taken relative to ``$HOME/.config/sayod/``.
>>
>> For an option value ``mytask.x``, the following paths will be tried
>> in sequence, reading each existing file. Any conflicting keys are
>> taken from the more recent configuration while the previously
>> existing keys are retained \[[configparse Documentation for Python
>> 3.13.2](https://docs.python.org/3/library/configparser.html#configparser.ConfigParser)\]:
>>
>> * ``$HOME/.config/sayod/mytask.x``
>> * ``$HOME/.config/sayod/mytask``
>> * ``$HOME/.config/sayod/mytask.rc``
>> * ``$HOME/.config/sayod/mytask.ini``
>>
>> See also [the page about configuration files](docs/configuration)

The following commands are available for **sayod-backup**:

## Subcommands for creating backups

### copy

Copies files and directories using rsync.

### database

Dumps the tables of a database and makes a smallcommit.

### smallcommit

Creates a commit from the current working directory of a git repository.

> **--add**, **-a**
>> Specify additional paths that should be added to the repository.

### replace-git

Creates a commit from all files in a git working directory.

### zipped-git

Extracts the content of an archive file into a git repository and adds
them.

### grandcommit

Integrates the last commits in a repository into one commit only.

### squasher

Integrates commits from a given time period into one commit, rebasing
newer commits onto them.

> **--scope** monthly,weekly,daily
>> The time period whose commits will be squashed
>
> **--keep-previous**, **--no-keep-previous**
>> Squash the first commit in the range into its predecessor.
>
> **--push** force,yes,no
>> Push the new repository to its origin(s)

## Subcommands for communication / logging

### logreader

Serves excerpts from the remote log. Usually called by remotereader.

### receiver

Receives new entries for the remote log. Usually called by notify.

### notify

Creates notifications, both to the User and to the remote log. Possibly
calls receiver on a remote machine via SSH.

> **--level** abort,deadtime,fail,fatal,start,success
>> Level of this notification. See [notify](docs/notify).
>
> **notification_text**
>> Notification body

### remotereader

Reads contents from the remote log. Calls logreader on a remote machine
via SSH.

## Other Subcommands

### config

Extracts actual, interpolated configuration options.

> **--section**:
>> Configuration file section
>
> **--key**
>> Configuration file key
>
> **--default**
>> string to return if no entry found
