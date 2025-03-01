# Sayod /ˈseɪəd/: SAve Your Own Data.

> Say It: Backups are good!

**sayod** is a backup suite written in
[**Python**](https://www.python.org). It mostly uses
[**git**](https://git-scm.com) and [**rsync**](https://rsync.samba.org) for its
tasks and communicates via
[**ssh**](https://en.wikipedia.org/wiki/Secure_Shell). It may show
notifications with
[**libnotify**](https://gitlab.gnome.org/GNOME/libnotify) and interactive prompts with
[**PySide6**](https://pypi.org/project/PySide6/).

Configuration of backup jobs is done via job resource files which are
usually stored in ``$HOME/.config/sayod/``, but can be placed anywhere.

## Installation

```bash
$ pip install sayod
```

## Usage

**sayod**'s first entrypoint is **[sayod-backup](docs/sayod-backup.md)**. Lesser entrypoints are
**logreader** and **receiver** which are supposed to be called via SSH
on a different machine to handle [deadtime](docs/context) and [notification](docs/notification)

```ini
# file $HOME/.config/sayod/mytask.rc
[source]
path = /home/myself

[target]
path = /var/my_backups/

[rsync]
deadtime = 7 # weekly backups
```

```bash
$ sayod-backup --config mytask copy
$ # same thing:
$ sayod-backup --config $HOME/.config/sayod/mytask.rc copy
```
