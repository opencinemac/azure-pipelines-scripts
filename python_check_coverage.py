import sys
import pathlib
import argparse
from xml.etree import ElementTree as et

MODULE_DIR = pathlib.Path("./").absolute()

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(description="check coverage")
    arg_parser.add_argument(
        "--minimum",
        type=float,
        help="minimum coverage % required to build"
    )
    args = arg_parser.parse_args()

    minimum_coverage = args.minimum
    print(f"COVERAGE REQUIRED: {minimum_coverage * 100}%")

    coverage_path = (
        MODULE_DIR / "zdevelop" / "tests" / "_reports" / "coverage.xml"
    )

    cov_xml: et.Element = et.parse(coverage_path).getroot()
    package_info: et.Element = cov_xml.find(".//package[@name='.']")

    coverage = float(package_info.attrib["line-rate"])

    if coverage < minimum_coverage:
        cov_percent = coverage * 100
        error_message = (
            f"test coverage must exceed 85% to publish, "
            f"current coverage is {cov_percent}%\n"
        )
        print(error_message)
        sys.stderr.write(error_message)
