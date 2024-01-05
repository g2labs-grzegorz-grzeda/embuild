from os import getcwd, path, makedirs, scandir
from json import load as json_load, dump as json_dump
from shutil import rmtree
from subprocess import run, DEVNULL
from argparse import ArgumentParser
from vt100logging import vt100logging_init, D, I, E
from traceback import print_stack

EMBUILD_REPOSITORY: str = 'https://github.com/g2labs-grzegorz-grzeda/embuild-repository.git'
EMBUILD_REPOSITORY_FILE: str = 'repository.json'
LOCAL_REPOSITORY_PATH: str = '~/.embuild/repository'

PROJECT_FILE_NAME: str = 'project.json'

DEFAULT_LIBRARY_DESTINATION: str = 'libraries'

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
    result = run(cmd, cwd=cwd, stdout=None if is_verbose() else DEVNULL,
                 stderr=None if is_verbose() else DEVNULL, shell=True)
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
    parser = ArgumentParser(
        description='embuild - Embedded CMake build system for C/C++. Visit https://embuild.dev for more information.')
    parser.add_argument('-v', '--verbose',
                        action='store_true', default=False, help='Verbose output')
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('list', help='List available libraries')
    create_subparser = subparsers.add_parser('create', help='Create a project')
    create_subparser.add_argument('destination', help='Destination directory')
    subparsers.add_parser('init', help='Initialize the project')
    add_subparser = subparsers.add_parser('add', help='Add a library')
    add_subparser.add_argument('libraries', help='Library name', nargs='+')
    update_subparser = subparsers.add_parser(
        'update', help='Update the project')
    update_subparser.add_argument(
        '-c', '--clean', help='Perform clean update', action='store_true', default=False)
    run_subparser = subparsers.add_parser('run', help='Run a script')
    run_subparser.add_argument(
        'script', help='Name of the script in project.json["scripts"] with (optional) parameters', nargs='+')
    args = parser.parse_args()
    set_verbosity(args.verbose)
    return args


class Repository:
    def __init__(self) -> None:
        self._real_path = path.expanduser(LOCAL_REPOSITORY_PATH)
        if path.exists(self._real_path):
            D("Updating repository")
            run_process(f'git pull', cwd=self._real_path)
        else:
            D("First time cloning repository")
            run_process(
                f'git clone --depth 1 {EMBUILD_REPOSITORY} {self._real_path}')

        with open(path.join(self._real_path, EMBUILD_REPOSITORY_FILE)) as f:
            self._libraries = json_load(f)['libraries']

    def libraries(self) -> dict:
        return self._libraries


def does_main_project_exist() -> bool:
    return path.exists(path.join(getcwd(), PROJECT_FILE_NAME))


def does_project_exist_for_directory(directory: str) -> bool:
    return path.exists(path.join(directory, PROJECT_FILE_NAME))


def create_project_object(name: str, description: str, author: str, license: str) -> dict:
    return {
        'name': name,
        'description': description,
        'author': author,
        'license': license,
        'libraries': []
    }


def load_project_object(project_file_path: str = None) -> dict:
    project_file_full_path = path.join(getcwd(), PROJECT_FILE_NAME)
    if project_file_path is not None:
        project_file_full_path = project_file_path
    with open(project_file_full_path) as f:
        return json_load(f)


def run_project_preconditions(project: dict, working_directory: str = getcwd()):
    if 'preconditions' not in project:
        return
    name = path.basename(working_directory)
    I(f"Running preconditions for '{name}'")
    for precondition in project['preconditions']:
        run_process(precondition, working_directory)


def store_project_object(project: dict, project_file_path: str = None):
    project_file_full_path = path.join(getcwd(), PROJECT_FILE_NAME)
    if project_file_path is not None:
        project_file_full_path = project_file_path
    with open(project_file_full_path, 'w') as f:
        json_dump(project, f, indent=2)


def create_project_file(destination: str = None):
    if destination is None:
        destination = getcwd()
        name = path.basename(destination)
    name = path.basename(destination)
    I(f"Creating project '{name}'")
    project = create_project_object(
        name,
        description=input("Project description: "),
        author=input("Project author: "),
        license=input("Project license: ")
    )
    store_project_object(project, path.join(destination, PROJECT_FILE_NAME))


def perform_create(destination: str):
    name = path.basename(destination)
    if path.exists(destination):
        raise Exception(f"Directory with name '{name}' already exists")
    I(f"Creating project '{name}'")
    makedirs(path.join(destination, 'source'))
    create_project_file(destination)
    with open(path.join(destination, 'CMakeLists.txt'), 'w') as f:
        f.write(f'''cmake_minimum_required(VERSION 3.22)

enable_testing()

project({name})
add_library(${{PROJECT_NAME}} STATIC)

add_subdirectory(source)
add_subdirectory({DEFAULT_LIBRARY_DESTINATION})
''')
    with open(path.join(destination, 'source', 'CMakeLists.txt'), 'w') as f:
        f.write(f'''target_sources(${{PROJECT_NAME}} PRIVATE {name}.c)
target_include_directories(${{PROJECT_NAME}} PUBLIC ${{CMAKE_CURRENT_SOURCE_DIR}})
''')
    makedirs(path.join(destination, DEFAULT_LIBRARY_DESTINATION))
    with open(path.join(destination, DEFAULT_LIBRARY_DESTINATION, 'CMakeLists.txt'), 'w') as f:
        f.write('# Automatically generated by embuild - DO NOT EDIT!\n')
    with open(path.join(destination, 'source', f'{name}.c'), 'w') as f:
        f.write(f'''#include "{name}.h"
''')
    guard_name = f'{name.upper()}_H'.replace('-', '_')
    with open(path.join(destination, 'source', f'{name}.h'), 'w') as f:
        f.write(f'''#ifndef {guard_name}
#define {guard_name}
#ifdef __cplusplus
extern "C" {{
#endif // __cplusplus

#ifdef __cplusplus
}}
#endif // __cplusplus
#endif // {guard_name}
''')
    with open(path.join(destination, '.clang-format'), 'w') as f:
        f.write(f'''---
BasedOnStyle: Chromium
IndentWidth: 4
ColumnLimit: 120
''')
    with open(path.join(destination, '.gitignore'), 'w') as f:
        f.write(f'''build/
{DEFAULT_LIBRARY_DESTINATION}/
''')
    run_process(f'git init', cwd=destination)
    run_process(f'git add .', cwd=destination)
    run_process(f'git commit -m "Initial commit"', cwd=destination)


def perform_init():
    if does_main_project_exist():
        raise Exception("Project already exists")
    I("Initializing project")
    create_project_file()


def perform_add_library(library: str, repository: Repository):
    I(f"Adding library '{library}'")
    if library not in repository.libraries():
        raise Exception(f"Library '{library}' does not exist exist")
    project = load_project_object()
    if 'libraries' not in project:
        project['libraries'] = [library]
    elif library in project['libraries']:
        raise Exception(f"Library '{library}' is already added")
    else:
        project['libraries'].append(library)
    store_project_object(project)


def perform_add(libraries: list, repository: Repository):
    for library in libraries:
        try:
            perform_add_library(library, repository)
        except Exception as e:
            E(e)


def perform_list(repository: Repository):
    print("Available libraries:")
    for library in repository.libraries().keys():
        print(f"\t{library}")


class Library:
    def __init__(self, name: str, destination: str, repository: Repository) -> None:
        if 'git@' in name:
            self.repository = name
            self.name = name.split('/')[-1]
        elif '/' in name:
            self.repository = f'git@github.com:{name}'
            self.name = name.split('/')[-1]
        else:
            if name not in repository.libraries():
                raise Exception(f"Library '{name}' does not exist")
            self.repository = repository.libraries()[name]
            self.name = name
        self.destination = path.join(destination, self.name)

    def download(self):
        if not path.exists(self.destination):
            I(f"Cloning  '{self.name}'")
            run_process(
                f'git clone --depth 1 {self.repository} {self.destination}')
        else:
            I(f"Updating '{self.name}'")
            run_process(f'git pull', cwd=self.destination)


def get_libraries_from_project(project: dict) -> list:
    if 'libraries' not in project:
        return []
    return project['libraries']


def perform_update(repository: Repository, clean: bool = False):
    I("Updating project")
    project = load_project_object()
    run_project_preconditions(project)
    libraries = get_libraries_from_project(project)
    if not libraries:
        raise Exception("No libraries to update")
    libraries_dest_path_root = path.join(getcwd(), DEFAULT_LIBRARY_DESTINATION)
    if 'libraries_destination' in project:
        libraries_dest_path_root = path.join(
            getcwd(), project['libraries_destination'])
    if clean:
        rmtree(libraries_dest_path_root, ignore_errors=True)
    makedirs(libraries_dest_path_root, exist_ok=True)

    cloned = {}
    visted = set()

    for library in libraries:
        library_obj = Library(library, libraries_dest_path_root, repository)
        library_obj.download()
        cloned[library] = library_obj

    while True:
        libraries_to_visit = set(cloned.keys()).difference(visted)
        if not libraries_to_visit:
            break

        library_name = list(libraries_to_visit)[0]
        if does_project_exist_for_directory(cloned[library_name].destination):
            local_project = load_project_object(
                path.join(cloned[library_name].destination, PROJECT_FILE_NAME))
            run_project_preconditions(
                local_project, cloned[library_name].destination)
            for library in get_libraries_from_project(local_project):
                if library not in cloned:
                    local_library_obj = Library(
                        library, libraries_dest_path_root, repository)
                    local_library_obj.download()
                    cloned[library] = local_library_obj
        visted.add(library_name)

    I("Generating CMakeLists.txt")
    with open(path.join(libraries_dest_path_root, 'CMakeLists.txt'), 'w') as cmake_file:
        cmake_file.write(
            '# Automatically generated by embuild - DO NOT EDIT!\n')
        for library in visted:
            cmake_file.write(f'add_subdirectory({library})\n')

    if not clean:
        all_directories = set([f.path for f in scandir(
            libraries_dest_path_root) if f.is_dir()])

        cloned_paths = set(
            [cloned[library].destination for library in cloned.keys()])

        for to_be_deleted in all_directories.difference(cloned_paths):
            I(f"Deleting old '{path.basename(to_be_deleted)}'")
            rmtree(to_be_deleted, ignore_errors=True)


def perform_run(script: list):
    project = load_project_object()
    if 'scripts' not in project:
        raise Exception("No scripts defined")
    if script[0] not in project['scripts']:
        raise Exception(f"Script '{script[0]}' does not exist")
    run_process(project['scripts'][script[0]] + ' ' + ' '.join(script[1:]))


def main():
    try:
        args = parse_args()
        vt100logging_init('embuild', is_verbose())
        if args.command == 'init':
            perform_init()
        elif args.command == 'create':
            perform_create(args.destination)
        else:
            check_environment()
            repository = Repository()
            if args.command == 'list':
                perform_list(repository)
            else:
                if not does_main_project_exist():
                    raise Exception(
                        "Project file does not exist - initialize!")
                if args.command == 'add':
                    perform_add(args.libraries, repository)
                    perform_update(repository)
                elif args.command == 'update':
                    perform_update(repository, args.clean)
                elif args.command == 'run':
                    perform_run(args.script)
        I("DONE")
    except Exception as e:
        E(e)
        if is_verbose():
            print_stack()
        exit(1)


if __name__ == '__main__':
    main()
