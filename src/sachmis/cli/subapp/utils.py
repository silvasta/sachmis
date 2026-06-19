from sstcore.cli import SafeTyper, utils_app


def main() -> None:
    app()


# INFO: this below is sstcore.utils_app (no delete!)

app: SafeTyper = utils_app


if __name__ == "__main__":
    main()
