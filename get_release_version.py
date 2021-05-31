import subprocess
import pathlib
import re
import configparser
import sys
import enum
import os
import toml
from packaging import version
from typing import Tuple, List, Dict, Callable

# Regex for finding tagged versions in github
REGEX_VERSIONS_GIT = re.compile(r'refs/tags/v(?P<version>[\S]+)')

MODULE_DIR = pathlib.Path("./").absolute()

CONFIG_PATH = MODULE_DIR / "setup.cfg"


class Languages(enum.Enum):
    PYTHON = "PYTHON"
    GO = "GO"
    RUST = "RUST"
    ELIXIR = "ELIXIR"
    PYTHON_SERVICE = "PYTHON_SERVICE"


LANGUAGE = Languages(os.environ["PublishLanguage"].upper())


# GO - SCRIPTS
def list_versions_git(config: configparser.ConfigParser) -> List[str]:
    git_process = subprocess.Popen(
        ['git', 'ls-remote', '--tags'],
        cwd=str(MODULE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    result, result_err = git_process.communicate(timeout=30)
    exit_code = git_process.wait()

    result_str = result.decode()
    result_err_str = result_err.decode()

    if exit_code != 0:
        raise RuntimeError(f"Error getting tag list from git: '{result_err_str}'")

    return REGEX_VERSIONS_GIT.findall(result_str)


def update_go_files(version_value: str) -> None:
    pass


# # PYTHON - SCRIPTS
# def list_versions_pypi(config: configparser.ConfigParser) -> List[str]:
#     name: str = config.get("metadata", "name")
#     print(f"PACKAGE NAME:", name)
#
#     pip_command = f"pip install {name}==notaversion"
#     pip_command = shlex.split(pip_command)
#
#     pip_response: str = str(
#         subprocess.Popen(
#             pip_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
#         ).communicate()[1]
#     )
#     if not pip_response:
#         print("Pip did not respond.")
#         exit(1)
#
#     if "could not find a version" not in pip_response.lower():
#         error_message = "pip response unknown\n"
#         print(error_message)
#         sys.stderr.write(error_message)
#
#     versions_pattern = re.compile(r"\(from versions: (.+)\)")  # noqa: W605
#
#     try:
#         existing_versions: str = re.findall(versions_pattern, pip_response)[0]
#     except IndexError:
#         existing_versions = ""
#
#     return existing_versions.split(", ")


def update_python_files(version_value: str) -> None:
    """Updates version strings specific to python libraries."""
    version_file_path = next(MODULE_DIR.rglob("./**/_version.py"))
    version_file_contents = f'__version__ = "{version_value}"\n'

    version_file_path.write_text(version_file_contents)


def update_rust_files(version_value: str) -> None:
    cargo = toml.load("./Cargo.toml")
    cargo["package"]["version"] = version_value
    with pathlib.Path("./Cargo.toml").open("w") as f:
        toml.dump(cargo, f)


REGEX_ELIXIR_VERSION = re.compile(r"version: \"\d+\.\d+\.\d+\",")


def update_elixir_files(version_value: str) -> None:
    with pathlib.Path("./mix.exs").open("rw") as f:
        data = f.read()
        REGEX_ELIXIR_VERSION.sub(f"version: \"{version_value}\",", data)
        f.write(data)


# def list_versions_docker_hub(config: configparser.ConfigParser) -> List[str]:
#     service_name = config.get("metadata", "name")
#
#     # Registry URL
#     REGISTRY_URL = os.environ["REGISTRY_URL"]
#
#     # Docker ID
#     DOCKER_ID = os.environ["DOCKER_ID"]
#
#     # Docker PW
#     DOCKER_PASSWORD = os.environ["DOCKER_PASSWORD"]
#
#     url = f"https://{REGISTRY_URL}/v2/{service_name}/tags/list"
#     response = requests.get(url, auth=HTTPBasicAuth(DOCKER_ID, DOCKER_PASSWORD))
#
#     try:
#         existing_versions: List[str] = response.json()["tags"]
#     except KeyError as error:
#         if response.status_code != 404:
#             raise error
#         if "NAME_UNKNOWN" != response.json()["errors"][0]["code"]:
#             raise error
#         existing_versions = list()
#
#     return existing_versions


LIST_VERSION_FUNC_INDEX_TYPE = Dict[
    Languages, Callable[[configparser.ConfigParser], List[str]]
]

# We're going to use git for all version lists moving forward so that pypi, git,
# and the target packaging service are less likely to become de-synced.
LIST_VERSION_FUNCS: LIST_VERSION_FUNC_INDEX_TYPE = {
    Languages.PYTHON: list_versions_git,
    Languages.GO: list_versions_git,
    Languages.RUST: list_versions_git,
    Languages.ELIXIR: list_versions_git,
    Languages.PYTHON_SERVICE: list_versions_git,
}

# Functions to update library files with new version
UPDATE_FILES_FUNCS: Dict[Languages, Callable[[str], None]] = {
    Languages.PYTHON: update_python_files,
    Languages.GO: update_go_files,
    Languages.RUST: update_rust_files,
    Languages.ELIXIR: update_elixir_files,
    Languages.PYTHON_SERVICE: update_python_files,
}


# GENERAL HELPER FUNCS
def get_target_major_minor_from_config(
    parser: configparser.ConfigParser
) -> Tuple[int, int]:
    """Gets the target major and minor version from the setup.cfg file."""
    target_version: str = parser["version"]["target"]
    target_split = target_version.split(".")

    try:
        target_major, target_minor = int(target_split[0]), int(target_split[1])
    except (ValueError, IndexError):
        error_message = "Version:Current setting in setup.cfg is not major.minor format"
        sys.stderr.write(error_message)
        raise ValueError(error_message)

    return target_major, target_minor


def get_latest_git_tagged_patch_version(
    major_target: int, minor_target: int, config: configparser.ConfigParser
) -> int:
    """Gets the latest patch version for the target major and minor on github."""
    version_list_getter = LIST_VERSION_FUNCS[LANGUAGE]

    version_str_list = version_list_getter(config)

    # parse versions into list
    patch_latest = -1
    for version_string in version_str_list:
        try:
            version_parsed = version.parse(version_string)
        except version.InvalidVersion:
            continue

        if version_parsed.release is None:
            continue

        major_parsed = version_parsed.release[0]
        minor_parsed = version_parsed.release[1]

        # If this version is from a different major / minor pairing, move over it.
        if major_parsed != major_target or minor_parsed != minor_target:
            continue

        # If the patch version is the highest we have found yet, remember it.
        patch_parsed = version_parsed.release[-1]
        if patch_parsed > patch_latest:
            patch_latest = patch_parsed

    return patch_latest


def main():
    # Parse the config file.
    parser = configparser.ConfigParser()
    parser.read(str(CONFIG_PATH))

    # Get the major and minor version we are targeting from the config
    target_major, target_minor = get_target_major_minor_from_config(parser)

    # Get the latest patch version that's been released from git
    latest_patch = get_latest_git_tagged_patch_version(
        target_major, target_minor, parser
    )
    target_patch = latest_patch + 1

    # Concatenate the next patch version
    version_release = f"{target_major}.{target_minor}.{target_patch}"

    # Get function to update lib files other than the config.
    files_update_func = UPDATE_FILES_FUNCS[LANGUAGE]
    files_update_func(version_release)

    # Write the version we are releasing to the config.
    parser["version"]["release"] = version_release

    with CONFIG_PATH.open('w') as f:
        parser.write(f)

    # Set the variable through azure's logging variable mechanism
    print(f"##vso[task.setvariable variable=RELEASE_VERSION]{version_release}")


if __name__ == '__main__':
    main()
