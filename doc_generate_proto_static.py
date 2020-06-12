import sys
import pathlib
import subprocess
from configparser import ConfigParser

MODULE_DIR = pathlib.Path("./").absolute()
CONFIG_PATH = MODULE_DIR / "setup.cfg"


def load_cfg() -> ConfigParser:
    """
    loads library config file
    :return: loaded `ConfigParser` object
    """
    config = ConfigParser()
    config.read(CONFIG_PATH)
    return config


def make_proto_html():
    config = load_cfg()
    proto_files_string = config.get("docs.proto", "paths")
    proto_files = [f for f in proto_files_string.split("\n") if f]

    command = [
        "protoc",
        "--doc_out=./zdocs/source/_static",
        "--doc_opt=html,proto.html",
    ]
    command += proto_files

    proc = subprocess.Popen(command)

    _, _ = proc.communicate()
    sys.exit(proc.returncode)


if __name__ == '__main__':
    make_proto_html()
