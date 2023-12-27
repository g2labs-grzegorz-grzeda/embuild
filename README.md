# embuild
Embuild is a tool for C/CMake static library management.

Check out [this website](https://embuild.dev/) for more details about available public libraries!

## Installation
Prerequirements:
- [git](https://git-scm.com/downloads)
- [cmake](https://cmake.org/download/)
- [ninja build](https://ninja-build.org/)

Install `embuild`: [`pip install -U embuild`](https://pypi.org/project/embuild/)

## Usage
### List available public libraries
`python -m embuild list`


### Create a project
`python -m embuild create <PROJECT-NAME>`

This creates:
- `<PROJECT-NAME>` directory
- `CMakeLists.txt` with a `<PROJECT-NAME>` library declaration
- `source` subdirectory with `<PROJECT-NAME>.h/.c` files and `CMakeLists.txt` file
- `project.json` embuild project file

### Initialize current directory
`python -m embuild init`

This creates:
- `project.json` embuild project file

### Add libraries
`python -m embuild add <LIB-1> .. <LIB-N>`

This:
- updates `project.json` with mentioned libraries
- creates a library subdirectory
- downloads relevant libraries and updates present ones
- (re)generates the `CMakeLists.txt` in the subdirectory 

### Update libraries
`python -m embuild update`

This:
- downloads/updates libraries according to current `project.json` `libraries` content
- removes old libraries
- (re)generates the `CMakeLists.txt` in the subdirectory

## Library name
The library has three ways to be named:
1. `<library-name>` (e.g. `event-handler`) - short name
1. `<user-name>/<library-name>` (e.g. `grzegorz-grzeda/cli`) - long name
1. `<protocol>:<git-repository>/<library-name>` - full name

### 1. Short name
This name is looked up in the [embuild repository](https://github.com/g2labs-grzegorz-grzeda/embuild-repository) `repository.json` file.

### 2. Long name 
This name is looked up in the GitHub service. The path is `https://github.com/<user-name>/<repo-name>.git`.
This is a good fit for a **private library** if hosted on GitHub and the current computer is configured to establish a SSH connection,

### 3. Full name
This name is treated as a path to a custom git repository. This is a best fit for a **private library**. The actual name of the library in question is the last part of the repository path name.

## Copyright
Created by Grzegorz Grzęda. Distributed under MIT license