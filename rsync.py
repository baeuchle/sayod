import datetime
from pathlib import Path
import subprocess
import log

rlog = log.get_logger('rsync')

class RSync:
    def __init__(self):
        self.exe_args = ['rsync']
        self.options = []
        self.popen_args = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.stderr = ""
        self.stdout = ""
        self.returncode = None

    @property
    def out_len(self):
        return len(self.stdout)

    @property
    def err_len(self):
        return len(self.stderr)

    def run(self, sources=[""], target=""):
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

    def fill_options(self, **kwargs):
        self.options.extend(kwargs.pop('options', []))
        self.options.append('--partial')
        self.options.append('-v')
        self.options.append('-i')
        self.options.append('-a')
        if kwargs.pop('no_cross', '') == '-x':
            self.options.append('-x')
        ef = kwargs.pop('exclude_file', False)
        if ef:
            self.options.append(f'--exclude-from={ef}')

    def sudo(self, do_sudo):
        if not do_sudo:
            return
        rlog.warning('Using privileged rsync is deprecated, you should rather run this as a privileged user!')
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

    def save_output(self, config):
        outfile = datetime.datetime.now().strftime(config.find('rsync', 'outfile', ''))
        if outfile:
            with Path(outfile).open("w+") as out:
                out.write('\n'.join(self.stdout))
            self.short_out = f"output in {outfile}"

    def notify_result(self, notify):
        error = ' '.join(self.stderr)
        code = '{self.returncode}\n{error}'
        if self.returncode == 0:
            notify.success('\n'.join([self.short_out, error]))
        elif self.returncode in (23, 24):
            notify.success('\n'.join([
                f"Nicht alle Quelldateien konnten gelesen werden {self.returncode}",
                self.short_out, error
                ]))
        elif self.returncode == 20:
            notify.abort('\n'.join([f"Kopiervorgang abgebrochen {self.out_len}/{self.err_len} Zeilen", error]))
        elif self.returncode in (1, 2, 4, 6):
            notify.fatal(f"rsync falsch benutzt {code}")
        elif self.returncode in (3, 5, 10, 11, 12, 13, 14, 21, 22):
            notify.fail(f"rsync copy error {code}")
        elif self.returncode in (25, 35, 40):
            notify.fail(f"rsync other error {code}")
        else:
            notify.fail(f"Unknown rsync error {code}")

