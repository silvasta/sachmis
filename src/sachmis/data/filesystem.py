from pathlib import Path


class ProjectScanner:
    IGNORE_DIRS: set[str] = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "env",
        "target",  # Rust build dir
        "node_modules",  # JS nightmare
    }

    ALLOWED_EXTS: set[str] = {
        ".py",
        ".rs",
        ".md",
        ".json",
        ".yaml",
        ".toml",
    }

    root: Path = Path.home() / "latest-sachmis/src/sachmis"

    @classmethod
    def arboreal(cls):
        local_root: Path = cls.root / "data/arboreal"

        names: list[str] = [
            "base.py",
            "biome.py",
            "forest.py",
            "sprout.py",
            "tree.py",
        ]
        xml: str = cls.create_xml([local_root / name for name in names])

        output_file: Path = local_root / "summary.xml"
        output_file.write_text(xml)

    @classmethod
    def create_xml(cls, paths: list[Path]) -> str:
        xml_parts: list[str] = ["<codebase>"]

        for path in paths:
            try:
                content: str = path.read_text(encoding="utf-8")
                # Get the relative path for the XML tag
                rel_path = path.relative_to(cls.root)
                xml_parts.append(
                    f'  <file path="{rel_path}">\n{content}\n  </file>'
                )
            except UnicodeDecodeError:
                pass  # Skip accidental binary files

        xml_parts.append("</codebase>")
        return "\n".join(xml_parts)

    @classmethod
    def gather_code(cls, root_dir: Path) -> str:
        """Walks the directory, grabs valid files, and formats them as XML."""
        xml_parts = ["<codebase>"]

        # Using os.walk because it allows in-place modification of 'dirs'
        # to prevent traversing into blacklisted folders.
        import os

        for root, dirs, files in os.walk(root_dir):
            # IN-PLACE PRUNING: Remove bad dirs so os.walk ignores them
            dirs[:] = [d for d in dirs if d not in cls.IGNORE_DIRS]

            for file in files:
                path = Path(root) / file

                # Check if file matches our whitelist
                if path.suffix in cls.ALLOWED_EXTS:
                    # Skip lockfiles which are huge and useless for LLMs
                    if path.name in {
                        "poetry.lock",
                        "Cargo.lock",
                        "package-lock.json",
                    }:
                        continue

                    try:
                        content = path.read_text(encoding="utf-8")
                        # Get the relative path for the XML tag
                        rel_path = path.relative_to(root_dir)
                        xml_parts.append(
                            f'  <file path="{rel_path}">\n{content}\n  </file>'
                        )
                    except UnicodeDecodeError:
                        pass  # Skip accidental binary files

        xml_parts.append("</codebase>")
        return "\n".join(xml_parts)


if __name__ == "__main__":
    ProjectScanner.arboreal()
