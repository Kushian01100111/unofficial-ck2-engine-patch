#!/usr/bin/env python3
"""Copy CK2 local saves into another directory without overwriting either set."""
import argparse
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Existing CK2 save games directory")
    parser.add_argument("destination", type=Path, help="Existing destination for copied saves")
    args = parser.parse_args()

    try:
        source = args.source.resolve(strict=True)
        destination = args.destination.resolve(strict=True)
        if not source.is_dir() or not destination.is_dir() or source == destination:
            raise ValueError("Select two distinct existing directories")

        saves = sorted(
            path for path in source.iterdir()
            if path.suffix.lower() == ".ck2" and path.is_file() and not path.is_symlink()
        )
        # Casefold catches collisions even if the current filesystem is case-sensitive.
        reserved = {path.name.casefold() for path in destination.iterdir()}
        for save in saves:
            name = save.name.casefold()
            if name in reserved:
                raise ValueError(f"Save name collision: {save.name}. No files were copied.")
            reserved.add(name)

        for save in saves:
            target = destination / save.name
            with save.open("rb") as existing:
                with target.open("xb") as copied:
                    try:
                        shutil.copyfileobj(existing, copied)
                        copied.flush()
                    except BaseException:
                        copied.close()
                        target.unlink()
                        raise
        print(f"Copied {len(saves)} save(s) to {destination}")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
