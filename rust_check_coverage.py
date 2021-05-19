import pathlib
import sys
from configparser import ConfigParser
from xml.etree import ElementTree as et


CONFIG_PATH: pathlib.Path = pathlib.Path(__file__).parent.parent.parent / "setup.cfg"
COVERAGE_XML = pathlib.Path("./zdevelop/tests/_reports/cobertura.xml")


def load_cfg() -> ConfigParser:
    """
    loads library config file
    :return: loaded `ConfigParser` object`
    """
    config = ConfigParser()
    config.read(CONFIG_PATH)
    return config


if __name__ == '__main__':
    config = load_cfg()

    minimum_coverage = config.getfloat("testing", "coverage_required", fallback=0.85)
    print(f"COVERAGE REQUIRED: {minimum_coverage * 100}%")

    cov_xml: et.Element = et.parse(COVERAGE_XML).getroot()
    coverage = float(cov_xml.attrib["line-rate"])

    if coverage < minimum_coverage:
        cov_percent = coverage * 100
        error_message = (
            f"test coverage must exceed {minimum_coverage * 100}% to publish, "
            f"current coverage is {cov_percent}%\n"
        )
        print(error_message)
        sys.stderr.write(error_message)
