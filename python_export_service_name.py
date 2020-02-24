import sys
import pathlib
import configparser


def load_cfg(config_path: pathlib.Path) -> configparser.ConfigParser:
    """
    loads library config file
    :return: loaded `ConfigParser` object
    """
    config = configparser.ConfigParser()
    config.read(str(config_path))
    return config


def main():
    config = load_cfg(pathlib.Path("./setup.cfg").absolute())

    # Get the name from the config.
    service_name = config.get("metadata", "name")

    # set a variable using azure's syntax.
    script = f"echo ##vso[task.setvariable variable=SERVICE_NAME]{service_name}"
    sys.stdout.write(script)


if __name__ == "__main__":
    main()
