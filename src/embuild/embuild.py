from os import getcwd, path, makedirs
from json import load as json_load
from shutil import rmtree
from subprocess import run, PIPE, DEVNULL, STDOUT
from argparse import ArgumentParser
from vt100logging import vt100logging_init, D, I, E

EMBUILD_REPOSITORY: str = 'git@github.com:g2labs-grzegorz-grzeda/embuild-repository.git'
EMBUILD_REPOSITORY_FILE: str = 'repository.json'
LOCAL_REPOSITORY_PATH: str = '~/.embuild/repository'

VERBOSITY: bool = False


def set_verbosity(is_verbose: bool) -> None:
    global VERBOSITY
    VERBOSITY = is_verbose


def is_verbose() -> bool:
    return VERBOSITY


def run_process(cmd: str, cwd: str = getcwd()) -> None:
    """Run a process and return its output."""
    if is_verbose():
        D(f"Running: '{cmd}'")
    result = run(cmd, cwd=cwd, stdout=PIPE if is_verbose() else DEVNULL,
                 stderr=STDOUT if is_verbose() else DEVNULL, shell=True)
    if result.returncode != 0:
        raise Exception(f"Failed to run: '{cmd}'")


def check_for(cmd: str):
    try:
        run_process(f'{cmd} --version')
    except Exception as e:
        raise Exception(f"{cmd} is not installed: {e}")


def check_environment():
    I("Checking environment")
    check_for('git')
    check_for('cmake')
    check_for('ninja')


def parse_args():
    parser = ArgumentParser(description='Builds the project')
    parser.add_argument('-v', '--verbose',
                        action='store_true', default=False, help='Verbose output')
    args = parser.parse_args()
    set_verbosity(args.verbose)
    return args


class Repository:
    def __init__(self) -> None:
        self._real_path = path.expanduser(LOCAL_REPOSITORY_PATH)
        if path.exists(self._real_path):
            run_process(f'git pull', cwd=self._real_path)
        else:
            run_process(
                f'git clone --depth 1 {EMBUILD_REPOSITORY} {self._real_path}')

        with open(path.join(self._real_path, EMBUILD_REPOSITORY_FILE)) as f:
            self._libraries = json_load(f)['libraries']

    def libraries(self) -> dict:
        return self._libraries


def main():
    vt100logging_init('embuild')
    try:
        parse_args()
        check_environment()
        repository = Repository()
        I("DONE")
    except Exception as e:
        E(e)
        exit(1)


if __name__ == '__main__':
    main()
