import logging
import os
from pathlib import Path
import subprocess

from .config import Config
from .gitversion import Git
from .notify import Notify, oneline
from .small_commit import make_small_commit

dblog = logging.getLogger(__name__)

class _Database:
    def __init__(self):
        self.type = Config.get().find('database', 'type', 'sqlite3')
        self.dumpdir = Config.get().find('database', 'directory', Path.cwd())
        self.dumppath = Path(self.dumpdir)
        self.source = Config.get().find('database', 'source', None)
        if not self.source:
            Notify.get().fatal(
                    "Kann Datenquelle nicht bestimmen (sollte in database::source stehen)")
            raise SystemExit(1)
        self.env = os.environ
        dblog.info("Dumping %s database %s to %s", self.type, self.source, self.dumpdir)
        self.tblcmd = []
        self.dumpcmd = []

    def prepare_dumps(self, **kwargs):
        if self.type == 'sqlite3':
            if not Path(self.source).exists():
                Notify.get().fatal(f'Database source {self.source} not found')
                raise SystemExit(1)
            self.tblcmd = ['sqlite3', self.source, '.tables']
            self.dumpcmd = ['sqlite3', self.source, '.dump {}']
        if self.type == 'mysql':
            self.env['MYSQL_PWD'] = kwargs.get('password', '')
            username = kwargs.get('username', '')
            hostname = kwargs.get('hostname', 'localhost')
            userarg = '--user='+username
            hostarg = '--host='+hostname
            self.tblcmd = ['mysql', userarg, hostarg, self.source, '-BNe', 'show tables']
            self.dumpcmd = ['mysqldump', userarg, hostarg, '--skip-extended-insert',
                '--skip-dump-date', self.source, '{}']
        dblog.info("Table command: '%s'", "' '".join(self.tblcmd))
        dblog.info("Dump  command: '%s'", "' '".join(self.dumpcmd))

    def dump(self, table_name):
        dblog.info("Dumping table %s", table_name)
        target = (self.dumppath / table_name).with_suffix('.sql')
        with open(target, 'w+b') as outf:
            with subprocess.Popen([arg.format(table_name) for arg in self.dumpcmd],
                    stdout=outf,
                    stderr=subprocess.PIPE,
                    env=self.env) as dump_proc:
                errors = dump_proc.stderr.read()
                if dump_proc.wait() != 0:
                    Notify.get().fatal(f"Table {table_name} in {self.source} could not be dumped:\n"
                                   + oneline(errors))
        return target

    def dump_all(self):
        files = []
        Notify.get().start(f'Database dump {self.source} started')
        sqltables = subprocess.run(self.tblcmd, capture_output=True, env=self.env, check=False)
        if sqltables.returncode != 0:
            Notify.get().fatal(f"Database table list cannot be read:\n{oneline(sqltables.stderr)}")
            raise SystemExit(1)
        for table_bytes in sqltables.stdout.split():
            target = self.dump(table_bytes.decode('utf-8'))
            files.append(target)
        return files

class Database:
    @classmethod
    def add_subparser(cls, sp):
        _ = sp.add_parser('database',
            help="""Dumps a database and make a small commit""")

    @classmethod
    def standalone(cls, _):
        d = _Database()
        d.prepare_dumps(
            password=Config.get().find('database', 'password', ''),
            username=Config.get().find('database', 'user', Config.get().find('env', 'LOGNAME', '')),
            hostname=Config.get().find('database', 'host', 'localhost')
        )
        file_list = d.dump_all()

        if not Config.get().find('git', 'commit', False):
            Notify.get().success("Database dump complete without source control")
            raise SystemExit(0)

        git = Git(Config.get().find('git', 'directory', d.dumpdir))
        make_small_commit(git, addables=file_list)
