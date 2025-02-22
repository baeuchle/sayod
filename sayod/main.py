import logging

from .arguments import Arguments, SayodCommandNotFound
from .config import Config
from .context import Context
from .log import Log
from .notify import Notify
from .version import __version__

mlog = logging.getLogger('sayod.main')


def _run():
    cli_args = Arguments()
    args_dict = cli_args.get_arguments()
    Config.init(**args_dict)
    Log.init(**args_dict, name=Config.get().find('info', 'stripped_name', None))
    subcommand = args_dict['subcommand']
    command_klass = Arguments.command_dict.get(subcommand, False)
    mlog.info("Executing sayod-backup (v%s) with %s", __version__, subcommand)
    Notify.init(**args_dict)

    if not command_klass:
        raise SayodCommandNotFound(f"Subcommand {subcommand} not found")
    mlog.info("Subcommand %s found", subcommand)

    if not Context.test_deadtime(**args_dict) and subcommand not in ['analyse']:
        return True
    with Context(subcommand) as _:
        result = command_klass.standalone(**args_dict)
    # may be string, boolean, or list (or something else)
    if isinstance(result, bool):
        return result
    if isinstance(result, list):
        result = '\n'.join([str(x) for x in result])
    if getattr(command_klass, 'print_result', False) and result:
        mlog.info("Result: %s", result)
        print(result)
    if getattr(command_klass, 'fail_empty_result', False) and not result:
        return False
    return True


def run():
    try:
        _run()
    except Exception as e:
        mlog.info("Notify is: %s", Notify._instance)
        mlog.exception("Program failed hard")
        if Notify.get():
            Notify.get().fatal("Sayod failed hard:", str(e))
        print(e)


if __name__ == '__main__':
    run()
