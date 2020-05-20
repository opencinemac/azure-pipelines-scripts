import sys
import pathlib
import configparser
from xml.etree import ElementTree as et

MODULE_DIR = pathlib.Path("./").absolute()


def load_cfg(config_path: pathlib.Path) -> configparser.ConfigParser:
    """
    loads library config file
    :return: loaded `ConfigParser` object
    """
    config = configparser.ConfigParser()
    config.read(str(config_path))
    return config


if __name__ == "__main__":
    # Get the main package name.
    config = load_cfg(pathlib.Path("./setup.cfg").absolute())

    minimum_coverage = config.getfloat("testing", "coverage_required", fallback=0.85)
    print(f"COVERAGE REQUIRED: {minimum_coverage * 100}%")

    coverage_path = (
        MODULE_DIR / "zdevelop" / "tests" / "_reports" / "coverage.xml"
    )

    cov_xml: et.Element = et.parse(coverage_path).getroot()
    package_info: et.Element = cov_xml.find(f".//package[@name='.']")

    coverage = float(package_info.attrib["line-rate"])

    if coverage < minimum_coverage:
        cov_percent = coverage * 100
        error_message = (
            f"test coverage must exceed {minimum_coverage * 100}% to publish, "
            f"current coverage is {cov_percent}%\n"
        )
        print(error_message)
        sys.stderr.write(error_message)
