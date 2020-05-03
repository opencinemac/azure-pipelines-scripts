import re
import sys
import pathlib
import subprocess
from configparser import ConfigParser

MODULE_DIR = pathlib.Path("./").absolute()

CONFIG_PATH = MODULE_DIR / "setup.cfg"

STD_OUT_LOG = pathlib.Path("./reports/test_stdout.txt")
STD_ERR_LOG = pathlib.Path("./reports/test_stderr.txt")
COVERAGE_LOG = pathlib.Path("./reports/coverage.out")
TEST_REPORT = pathlib.Path("./reports/test_report.html")
COVERAGE_REPORT = pathlib.Path("./reports/coverage.html")

COVERAGE_REGEX = re.compile(r"total:\s+\(statements\)\s+(\d+\.\d)%")


def load_cfg() -> ConfigParser:
    """
    loads library config file
    :return: loaded `ConfigParser` object
    """
    config = ConfigParser()
    config.read(CONFIG_PATH)
    return config


def run_test():
    config = load_cfg()
    coverage_required = config.getfloat("testing", "coverage_required")
    sys.stdout.write(f"COVERAGE REQUIRED: {coverage_required}\n")

    command = [
        "go",
        "test",
        "-v",
        "-failfast",
        "-covermode=count",
        f"-coverprofile={COVERAGE_LOG}",
        "-coverpkg=./...",
        "./...",
    ]

    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout, stderr = proc.communicate()

    sys.stdout.write(stdout)
    sys.stderr.write(stderr)

    STD_OUT_LOG.write_text(stdout)
    STD_ERR_LOG.write_text(stderr)

    if proc.returncode != 0:
        sys.exit(proc.returncode)

    # Use the cov command to generate the total coverage
    command = [
        "go",
        "tool",
        "cover",
        "--func",
        COVERAGE_LOG,
    ]

    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout, stderr = proc.communicate()

    sys.stdout.write(stdout)
    sys.stderr.write(stderr)

    with STD_OUT_LOG.open("a") as f:
        f.write(stdout)
    with STD_ERR_LOG.open("a") as f:
        f.write(stderr)

    if proc.returncode != 0:
        sys.exit(proc.returncode)

    # Get the last coverage tally in the result
    coverage_str = [x for x in COVERAGE_REGEX.finditer(stdout)][-1].group(1)
    coverage = float(coverage_str)

    if coverage < coverage_required:
        sys.stderr.write(
            f"Coverage {coverage} is less than required {coverage_required}\n"
        )
        sys.exit(1)
    else:
        sys.stderr.write(
            f"Coverage {coverage}% passes requirement of {coverage_required}%\n"
        )


if __name__ == '__main__':
    run_test()
