import datetime
import logging

from .config import Config
from .notify import Notify
from .remotereader import remote, LAST

dlog = logging.getLogger(__name__)

class DeadTime:
    @classmethod
    def add_options(cls, parser):
        parser.add_argument('--force', '-f',
                            default=False,
                            action='store_true',
                            required=False,
                            help="Ignore deadtime and force action",
                            dest="deadtime_force")

    @classmethod
    def test(cls, force):
        deadtime = int(Config.get().find('rsync', 'deadtime', 0))
        if deadtime <= 0:
            dlog.debug("No deadtime given, going ahead")
            return True
        last_success = remote('SUCCESS', LAST)
        tage = (datetime.datetime.today() - last_success).days
        if tage > deadtime:
            dlog.info("Deadtime is over")
            return True
        if not force:
            Notify.get().deadtime(
                    f"Letztes erfolgreiches Backup war vor weniger als {deadtime} Tagen")
            return False
        dlog.info("Deadtime ignored because --force was specified")
        return True
