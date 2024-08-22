#!/usr/bin/env python3
"""
Datagen - Generate routes summary per country.
"""

import argparse
import asyncio
import sys

from dgen.datagen import Datagen


async def main():
    """Datagen"""
    parser = argparse.ArgumentParser(
        description="Datagen - Generate routes summary per country."
    )
    parser.add_argument(
        "-lg",
        action="store",
        dest="lg",
        metavar="ALICE_URL",
        help="Datagen - Generate routes summary per country.",
    )
    parser.add_argument(
        "-a",
        action="store_true",
        dest="all",
        help="Generate routes summary per country for all IXPS @ datagen/config.yaml.",
    )

    args = parser.parse_args()
    options = all(value is True for value in vars(args).values())

    datagen = Datagen()

    if args.lg:
        await datagen.alice_host(args.lg)

    if args.all:
        ixps = datagen.load_yaml()
        await datagen.process_all_ixps_concurrently(ixps)

    if not options:
        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted")
