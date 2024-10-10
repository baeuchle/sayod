import datetime
import logging
from pathlib import Path
import subprocess

from .config import Config
from .notify import Notify

rlog = logging.getLogger(__name__)

class RSync:
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        self.config = Config.get().find_section('rsync')
        self.exe_args = ['rsync']
        self.options = []
        self.fill_options()
        self.popen_args = {'stdout':subprocess.PIPE, 'stderr':subprocess.PIPE, 'text':True}
        self.stderr = ""
        self.stdout = ""
        self.returncode = None
        self.short_out = ""
        self.sudo()

    @property
    def out_len(self):
        return len(self.stdout)

    @property
    def err_len(self):
        return len(self.stderr)

    def run(self, sources=None, target=""):
        if sources is None:
            sources = [""]
        rsync_args = [*self.exe_args, *self.options, *sources, target]
        with subprocess.Popen(rsync_args, **self.popen_args) as proc:
            rlog.info("rsync is running...")
            (out, err) = proc.communicate()
            proc.wait()
            rlog.info("rsync has finished.")
        self.stdout = out.strip().split('\n')
        self.stderr = err.strip().split('\n')
        self.returncode = proc.returncode
        self.short_out = f"{self.out_len} output lines"

    def fill_options(self):
        self.options.extend(self.config.get('options', '').split())
        self.options.append('--partial')
        self.options.append('-v')
        self.options.append('-i')
        self.options.append('-a')
        if self.config.get('no_cross', '') == '-x':
            self.options.append('-x')
        ef = self.config.get('exclude_file', False)
        if ef:
            self.options.append(f'--exclude-from={ef}')

    def sudo(self):
        if not self.config.get('privilege', False):
            return
        rlog.warning('Using privileged rsync is deprecated,' +
            ' you should rather run this as a privileged user!')
        self.exe_args.insert(0, 'sudo')
        self.popen_args['stdin'] = subprocess.PIPE

    def report_output(self):
        rlog.debug("output: ##############")
        for x in self.stdout:
            rlog.debug(x)
        rlog.debug("error: ###############")
        for x in self.stderr:
            rlog.debug(x)
        rlog.debug("######################")

    def save_output(self):
        outfile = datetime.datetime.now().strftime(self.config.get('outfile', ''))
        if outfile:
            with Path(outfile).open("w+", encoding='utf-8') as out:
                out.write('\n'.join(self.stdout))
            self.short_out = f"output in {outfile}"

    def notify_result(self):
        rlog.info("RSYNC done, exit code %d, %d log lines, %d error lines",
            self.returncode, self.out_len, self.err_len)
        error = ' '.join(self.stderr)
        code = f'{self.returncode}\n{error}'
        if self.returncode == 0:
            Notify.get().success('\n'.join([self.short_out, error]))
        elif self.returncode in (23, 24):
            Notify.get().success('\n'.join([
                f"Nicht alle Quelldateien konnten gelesen werden {self.returncode}",
                self.short_out, error
                ]))
        elif self.returncode == 20:
            Notify.get().abort('\n'.join(
                [f"Kopiervorgang abgebrochen {self.out_len}/{self.err_len} Zeilen", error]))
        elif self.returncode in (1, 2, 4, 6):
            Notify.get().fatal(f"rsync falsch benutzt {code}")
        elif self.returncode in (3, 5, 10, 11, 12, 13, 14, 21, 22):
            Notify.get().fail(f"rsync copy error {code}")
        elif self.returncode in (25, 35, 40):
            Notify.get().fail(f"rsync other error {code}")
        else:
            Notify.get().fail(f"Unknown rsync error {code}")

    def wrapup(self):
        self.save_output()
        self.notify_result()
        self.report_output()
