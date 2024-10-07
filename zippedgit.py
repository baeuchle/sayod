from datetime import datetime
from pathlib import Path
import logging
from subprocess import run

import regex as re

from config import Config
from gitversion import Git

zglog = logging.getLogger('backup.zipped-git')

class _ZippedGit:
    def __init__(self, gitdir):
        self.git = Git(gitdir)
        directory = Path(Config.get().find('zipstore', 'path', gitdir.parent))
        pattern = Config.get().find('zipstore', 'pattern', 'backup_*.zip')
        self.finder = re.compile(Config.get().find('zipstore', 'date_expression', None))
        self.files = sorted(list(directory.glob(pattern)))

    def run(self):
        for bf in self.files:
            zglog.debug("Looing at file %s", bf.stem)
            tokens = self.finder.findall(bf.stem)
            if not tokens:
                zglog.warning("file %s doesn't match %s", bf, self.finder)
                continue
            self.process_file(bf, tokens)

    def process_file(self, file, tokens):
        if Config.get().find('zipstore', 'use_timestamp', False):
            zipdata = datetime.fromtimestamp(int(tokens[0]))
        else:
            zipdata = datetime.now()
        for gitfile in self.git.commandlines('ls-files'):
            gitfile = gitfile.strip()
            self.git.command('rm', gitfile)
            print(".", end="", flush=True)
        print(" now unzipping")
        zipargs = ["7z", "-y", "-o" + str(self.git.cwd)]
        password = Config.get().find('zipstore', 'password', None)
        if password:
            zipargs.append('-p'+password)
        zipargs.append('x')
        zipargs.append(str(file))
        _ = run(zipargs, check=False) # TODO use error handling
        self.git.command('add', '.')
        self.git.command('commit', '-m', f"BACKUP {zipdata:%Y-%m-%d}\n\nfrom file {file.stem}")

class ZippedGit:
    @classmethod
    def add_subparser(cls, sp):
        sp.add_parser('zipped-git',
            help='Unpack a zip file and use its contents to replace a git working directory.'
        )

    @classmethod
    def standalone(cls, _):
        gitdir = Path(Config.get().find('repository', 'path', '.'))
        zg = _ZippedGit(gitdir)
        zg.run()
