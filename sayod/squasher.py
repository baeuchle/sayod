import argparse
import logging

from .config import Config
from .gitversion import Git, STDOUT
from .scope import Scope

slog = logging.getLogger(__name__)

class _Squasher:
    def __init__(self, args):
        self.git = Git(Config.get().find('target', 'path', None), stderr=STDOUT)
        self.sc = Scope(args.scope, args.keep_previous)
        self.squashables = set()

    def handle(self):
        output = self.git.commandlines('rev-list',
                                       f'--before={self.sc.end_string}',
                                       f'--after={self.sc.start_string}', 'HEAD')
        self.squashables = {x.strip() for x in output}

        if not self.squashables:
            slog.info("No commits found between %s and %s.",
                      self.sc.start_string, self.sc.end_string)
            return
        slog.info("Found %d commits between %s and %s",
                  len(self.squashables), self.sc.start_string, self.sc.end_string)
        first_commit = output[-1].strip()
        initial_commit =  self.git.command('rev-list', '--max-parents=0', 'HEAD').strip()

        if self.sc.keep_previous and first_commit == initial_commit:
            slog.info("Repository is not old enough for this backup scope.")
            return

        # rebase onto one commit before first_commit, so that all the commits can be squashed into
        # that one.
        base = "^" if self.sc.keep_previous else ""
        prepare_output = self.git.command('-c', 'core.editor=echo break | tee', 'rebase', '-i',
                                          first_commit + base)
        if self.git.returncode != 0:
            slog.error("git rebase failed: %s", prepare_output)
            return
        # this has created an empty file in .git/rebase-merge/git-rebase-todo (had 'break', but that
        # is already done) and a non-empty file in .git/rebase-merge/git-rebase-todo.backup
        self.make_rebase_plan()

        rb_continue_output = self.git.command('rebase', '--continue')
        if self.git.returncode != 0:
            slog.error("git rebase --continue failed: %s", rb_continue_output)
            abort_output = self.git.command('rebase', '--abort')
            if self.git.returncode != 0:
                slog.error("Cannot even abort rebase: %s", abort_output)

    def make_rebase_plan(self):
        rebase_plan = []
        new_todo_file =  self.git.cwd / '.git' / 'rebase-merge' / 'git-rebase-todo'
        orig_todo_file = new_todo_file.with_suffix('.backup')
        with orig_todo_file.open() as rebase_plan_file:
            for line in rebase_plan_file:
                self.handle_line(line, rebase_plan)
        with new_todo_file.open('w') as new_plan:
            new_plan.write('\n'.join(rebase_plan))

    def handle_line(self, line, result):
        stripped = line.strip()
        if not stripped:
            return
        if stripped == 'noop':
            result.append(stripped)
            return
        if stripped[0] == '#':
            return
        words = stripped.split()
        if words[1] in self.squashables:
            words[0] = 'fixup'
            self.squashables.remove(words[1])
            result.append(' '.join(words))
            # this is only necessary for the last fixup'ed commit, but it is fast and doesn't really
            # hurt to do multiple times.
            result.append(f'exec GIT_COMMITTER_DATE="{self.sc.end_date:%Y-%m-%d:%H:%M:%S}" ' +
                          f'git commit --amend --no-edit --date="{self.sc.end_string}" ' +
                          f'-m "{self.sc.scope} backup from {self.sc.end_string}"')
        else:
            result.append(stripped)
            result.append('exec GIT_COMMITTER_DATE="$(git log -1 --format=%ad)" ' +
                          'git commit --amend --no-edit ' +
                          '--date="$(git log -1 --format=%ad)"')


class Squasher:
    @classmethod
    def add_subparser(cls, sp):
        ap = sp.add_parser('squasher', help='''Squashes backups inside a git repository so that
            different backup ages remain. The idea is to regularly make a backup, commit everything
            to git. (This needs to be done independent of this program.) Then, run this program with
            a given --scope and it will squash all commits in the previous $scope, leaving one
            commit only. Depending on --keep_previous, the new commit will replace the commit just
            previous to the last $scope, or it will simply follow that one. Commits newer than the
            previous scope (e.g., commits from this month for $scope == month) will be as untouched
            as possible (i.e., their dates are kept, their hashes not).''',
            epilog='All of this only makes sense if you also run git gc regularly.')
        ap.add_argument('--scope', choices='monthly weekly daily'.split(), required=True)
        ap.add_argument('--keep-previous', action=argparse.BooleanOptionalAction, default=None,
            help='''Squash the first commit in the range into its previous commit. This should only
            be activated at the longest interval that is used for the given repository. If not
            given, the default value depends on --scope: for monthly: True, for weekly and daily:
            False.''')

    @classmethod
    def standalone(cls, args):
        sq = _Squasher(args)
        sq.handle()
