# Context

**sayod** can automatically provide context for the task at hand. With
these contexts, it is possible to prompt the user to plug in a backup
disk, automatically mount a network drive or other preparations. Some
providers may do their task after completion of the main task.

In configuration section ``[context]``, a key ``providers`` contains a
whitespace-separated list of context providers which are executed in the
order given before the core task and destroyed in reverse order.

For each provider, a config section of the same name must exist which
contains details about this provider.

If providing one such context fails, neither subsequent providers nor the
main are executed, but clean-up happens for all providers that have been
provided.

Providers are not executed for subcommand 'analyse'. This list should
also include 'config' and other commands.

````ini
[rsync]
deadtime = 5

[context]
providers = named_provider_1 named_provider_2

[named_provider_1]
action = manual

[named_provider_2]
action = semaphore
````

## deadtime

One special 'provider' is **deadtime**, which is currently not included
in providers, but works similarly: if ``[rsync]`` contains ``deadtime``
with an integer value, the execution only happens if the last successful
execution is more than that many days ago, as [read from the remote
log](remotereader.md). Execution may be forced with [command line
option](sayod-backup.md#command-line-usage) **--force**.

The rational behind deadtime is that we might want to try to catch the
users attention at regular intervals, because they might be unattentive,
away from keyboard or what have you. A cronjob with a high frequency
will ensure that the backup is tried while they are available, but after
a successful backup, we don't want to bother them too soon *again*.

## Providers

Each provider section (``[named_provider_*]`` in the above example) needs
to have a key ``action`` which determines the type of action needed for
this provider. Further configuration depends on this type.

**Common** configuration options are:

- **action**: type of the provider, see below
- **unless**: references a [Tester](context.md#testers) which, if its
  test succeeds, skips this provider. If not given,
  [NoneTester](#nonetester) is used.
- **postrequisite**: references a Tester which tests for a condition
  after this provider's action has taken place. If it is **not** met,
  the provider fails. By default, the tester chosen in **unless**
  determines the matching post Tester.

### Manual Provider

**Triggered by:** action = manual

Prompts the user for some action which they should take. If a GUI and
PySide is available, a message box pops up; else, the prompt appears on
STDOUT.

Valid configuration options are:

* **title** for the title of the message box
* **message** for its contents
* **timeout** (floating point value) for the time in seconds until the
  windows times out (without further action).

Since no automatic action takes place, no clean-up is performed.

### SSHFS Provider

**Triggered by:** action = sshfs

Mounts a remote directory with
[sshfs](https://github.com/libfuse/sshfs). This executes sshfs directly.

Valid configuration options are:

* **host** for the remote site's address. Defaults to 127.0.0.1 . Use
  without trailing colon, this will be added automatically.
* **user** for the user name to be used on the remote. If not given,
  then it is not passed to sshfs.
* **remote_port** for the TCP port with which to connect. Defaults to
* **remote_path** for the path on the remote machine which is to be
  mounted
* **mountopts** for a whitespace-separated list of options passed to
  sshfs' **-o** option.
* **local_path** for the local mount point.

If executed, then the clean-up unmounts **local_path** using
[fusermount](https://github.com/libfuse/libfuse) -u.

### ADB Provider

**Triggered by:** action = adb

Establishes an [adb](https://developer.android.com/tools/adb) connection
to some Android device. This might have to run before an adbfs provider.

Valid configuration options are:

* **device** fixes the Android device serial number (or TCP/IP address,
  if applicable) that adb uses to identify the device.

### ADBFS Provider

**Triggered by:** action = adbfs

Mounts a directory from some Android device with
[adbfs](https://github.com/spion/adbfs-rootless). This executes adbfs
directly.

Valid configuration options are:

* **device** fixes the Android device serial number (or TCP/IP address,
  if applicable) that adb uses to identify the device.
* **mountopts** for a whitespace-separated list of options passed to
  sshfs' **-o** option.
* **local_path** for the local mount point.

If executed, then the clean-up unmounts **local_path** using
[fusermount](https://github.com/libfuse/libfuse) -u.

### Directory Provider

**Triggered by:** action = mkdir

Creates a temporary directory.

Valid configuration options are:

* **dir** Path to the directory. Must not exist prior to execution! (Use
  together with **unless = [is_dir](#directorytester) PATH** to mitigate)

If executed, the clean-up **rmdir**s the directory. Therefore, it needs
to be empty before clean-up!

### Semaphore Provider

### Sayod Provider

## Testers

Testers are meant to make sure Providers actually need to be called and
that they actually succeeded. This may include testing for a mount point
or the existence of a directory, the availability of a network resource
etc.

Testers are specified in one line. The first word (split on whitespace)
is used to determine the type of Tester, while the remainder will be
passed to the specific tester.

### NoneTester

**Triggered by:** unless = none

Never fails; the provider can always run. No post provider checks are
performed.

### AlwaysTester

**Triggered by:** unless = always

Never succeeds, such that the provider always runs. Post provider checks
always succeed.

### MountpointTester

**Triggered by:** unless = mountpoint &lt;PATH&gt;

Succeeds if &lt;PATH&gt; is a mount point.

**NB:** PATH is first split up by whitespace, then joined by a single
space. That means that double spaces or differnt whitespace in PATH will
be handled incorrectly.

### DirectoryTester

**Triggered by:** unless = is_dir &lt;PATH&gt;

Succeeds if &lt;PATH&gt; is a directory.

**NB:** PATH is first split up by whitespace, then joined by a single
space. That means that double spaces or differnt whitespace in PATH will
be handled incorrectly.
