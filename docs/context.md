# Context

**sayod** can automatically provide context for the task at hand. With
these contexts, it is possible to prompt the user to plug in a backup
disk, automatically mount a network drive or perform other preparations.
Some providers may do their task after completion of the main task.

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
  [NoneTester](#nonetester) is used (which means the provider is never
  executed, see its documentation).
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
* **remote_port** for the TCP port with which to connect. Defaults to 22
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

**Triggered by:** action = semaphore

Control execution dependent on the existence of a file

Valid configuration options are:

* **file**: Path to the file. Defaults to /tmp/semaphore.
* **if_present**: (yes/no) Control if the provider should succeed if the
  given file is present or if it should fail. Default: no
* **toggle**: (yes/no) Toggle existence of the file (create if it
  doesn't exist, delete if it does). Default: yes

Semaphore Provider can be used if a chain of backups need to be executed
by different users (e.g., root copies data that your normal user then
needs to add into git). In that case, root may use

````ini
[turn_on_semaphore]
action = semaphore
file = /tmp/my_flag
if_present = no     # only begin if the file is not present
toggle = yes        # create file after completion
unless = always
````

and the normal user may use

````ini
[turn_off_semaphore]
action = semaphore
file = /tmp/my_flag  # same file
if_present = yes     # only begin if file is present → root has finished
toggle = yes         # delete after completion → root may start again.
unless = always
````

Currently, Semaphore Provider cannot be used for making sure only one
job runs. (see [#11](https://github.com/baeuchle/sayod/issues/11))

### Sayod Provider

**Triggered by:** action = sayod

Execute another sayod command before or after execution

Valid configuration options are:

* **command**: [Sayod
  command](/docs/sayod-backup/#subcommands-for-creating-backups) to be executed
* **before**: (yes/no) Control whether to execute before main execution.
  (Else, execution happens afterwards.) Default: yes

Execution **after** the main task only happens if the main task was
successful and if all inner providers were released successfully.

The sayod command started needs to be configured in the main
configuration. Conflicting configurations cannot be handled. Only
commands that do not require additional command line arguments are
permitted.

Example usages include putting all copied file into a git repository,
either by replacing, adding or unzipping:

````ini
[committer]
action = sayod
command = replace-git   # or smallcommit, zipped-git
before = no
unless = always
````

## Testers

Testers control if a [Provider](#providers) needs to run. If the tested
condition is met at the start (**prerequisite**), the provider **does
not run**. If the tested condition is not met after the provider ran
(**postrequisite**), **the provider failed**.

Each tester provides a default postrequisite, which is usually the same
test. For instance, a Provider may want to create a resource, but only
if that resource doesn't yet exist. After running the provider, the
resource *should* exist. Here, both **prerequisite** and
**postrequisite** tests are the same. However, a different
**postrequisite** may be chosen in the configuration of the provider.

Testers are specified in one line. The first word (split on whitespace)
is used to determine the type of Tester, while the remainder will be
passed to the specific tester.

### NoneTester

**Triggered by:** ``unless = none``

Never fails; the provider is never necessary. No post provider checks are
performed. This is the default behaviour for all
[Providers](#providers) -- you need to explicitly activate providers.
NoneTester is used as default **postrequisite** for [AlwaysTester](#alwaystester).

### AlwaysTester

**Triggered by:** ``unless = always``

Never succeeds, such that the provider always runs.
The default **postrequisite** is [NoneTester](#nonetester), so that a
provider with ``unless = always`` always runs and always succeeds.

### MountpointTester

**Triggered by:** ``unless = mountpoint <PATH>``

Succeeds if &lt;PATH&gt; is a mount point.

**NB:** PATH is first split up by whitespace, then joined by a single
space. That means that double spaces or different whitespace in PATH will
be handled incorrectly.

### DirectoryTester

**Triggered by:** ``unless = is_dir <PATH>``

Succeeds if &lt;PATH&gt; is a directory.

**NB:** PATH is first split up by whitespace, then joined by a single
space. That means that double spaces or different whitespace in PATH will
be handled incorrectly.
