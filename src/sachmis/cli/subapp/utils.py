from sstcore.cli import SafeTyper, utils_app

from ...config import SachmisConfig, get_config

config: SachmisConfig = get_config()


def main() -> None:
    app()


# LATER: move less needed stuff here

app: SafeTyper = utils_app


if __name__ == "__main__":
    main()
