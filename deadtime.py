import datetime

import log
import remotereader

dlog = log.get_logger('deadtime')

def add_options(parser, **kwargs):
    optname = kwargs.get('optname', 'force')
    parser.add_argument('--' + optname, '-' + optname[0],
                        default=False,
                        action='store_true',
                        required=False,
                        help="Ignore deadtime and force action",
                        dest="deadtime_force")

def test_deadtime(force, config, notify):
    deadtime = int(config.find('rsync', 'deadtime', 0))
    if deadtime <= 0:
        dlog.debug("No deadtime given, going ahead")
        return True
    last_success = remotereader.remote(config, notify, 'SUCCESS', remotereader.LAST)
    tage = (datetime.datetime.today() - last_success).days
    if tage > deadtime:
        dlog.info("Deadtime is over")
        return True
    if not force:
        notify.deadtime(f"Letztes erfolgreiches Backup war vor weniger als {deadtime} Tagen")
        return False
    dlog.info("Deadtime ignored because --force was specified")
    return True


