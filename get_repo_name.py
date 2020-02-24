import pathlib
import subprocess
import re


REGEX_REPO_NAME = re.compile(r"\/(?P<repo>[\w-]+)(.git)?\n")


MODULE_DIR = pathlib.Path("./").absolute()


if __name__ == '__main__':

    git_process = subprocess.Popen(
        ["git", "remote", "show", "origin"],
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

    print("Git Response:", result_str, sep="\n")

    repo_name = REGEX_REPO_NAME.findall(result_str)[0][0]

    print(f"##vso[task.setvariable variable=REPO_NAME]{repo_name}")
