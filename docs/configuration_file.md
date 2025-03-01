# Configuration files

Configuration files are expected to be in ini-file format. They are read
using
[configparser.ConfigParser](https://docs.python.org/3/library/configparser.html#module-configparser)
with [extended
Interpolation](https://docs.python.org/3/library/configparser.html#configparser.ExtendedInterpolation).

Each subcommand of **[sayod-backup](sayod-backup.md)** needs to be given
an option **--config &lt;FILE&gt;**.

For an option value ``mytask.x``, the following paths will be tried
in sequence, reading each existing file:

* ``$HOME/.config/sayod/mytask.x``
* ``$HOME/.config/sayod/mytask``
* ``$HOME/.config/sayod/mytask.rc``
* ``$HOME/.config/sayod/mytask.ini``

N.B. from [configparse Documentation for Python
3.13.2](https://docs.python.org/3/library/configparser.html#configparser.ConfigParser):
> Any conflicting keys are taken from the more recent configuration
> while the previously existing keys are retained.

After reading all files, a new ini-file section ``env`` is created which
contains all environment variables, only with ``$`` replaced by its
fullwidth form ``＄`` (because the regular dollar sign $ would lead to
interpolation attempts).

Then, all values listed in section \[defaults\] are taken to be file
names whose contents are read into the configuration; relative filenames
are relative to the main configuration file's path. Interpolation rules
still apply, but there is no recursion into the default's \[defaults\]
section. The key names in \[defaults\] are ignored and should be used
for information purposes only.

Finally, the four initial files are read *again* to ensure that the values
read through \[defaults\] are actually only defaults and can be
overwritten by the current configuration.

Interpolation happens at retrieval, but new environment variables aren't
read.

## Example

For the two configuration files

````ini
# mytask.rc
[defaults]
change_source = other.ini

[source]
path = /home
asdf = newvalue
````

and

````ini
# other.ini
[source]
asdf = xyz
jklö = qwer_${source:asdf}
````

the following values are provided:

````bash
$ sayod-backup --config mytask.rc config --section source --key path
/home
$ sayod-backup --config mytask.rc config --section source --key asdf
newvalue
$ sayod-backup --config mytask.rc config --section source --key jklö
qwer_newvalue
$ [[ "$(sayod-backup --config mytask.rc config --section env --key HOME)" == "$HOME" ]] && echo "env read correctly" || echo "wtf?"
env read correctly
````
