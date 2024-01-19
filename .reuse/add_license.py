# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

"""Helper script to add licenses to files.

This script can be used to apply the licenses and default copyright holders
to files in the repository.

It uses the short cuts from the ``.reuse/shortcuts.yaml`` file and
adds them to the call of ``reuse annotate``. Any command line option however
overwrites the config in ``shortcuts.yaml``

Usage::

    python .reuse/add_license.py <shortcut> <path> [OPTIONS]
"""

import os.path as osp
from argparse import ArgumentParser
from textwrap import dedent
from typing import Dict, Optional, TypedDict

import yaml
from reuse.project import Project
from reuse.vcs import find_root

try:
    from reuse._annotate import add_arguments as _orig_add_arguments
    from reuse._annotate import run
except ImportError:
    # reuse < 3.0
    from reuse.header import add_arguments as _orig_add_arguments
    from reuse.header import run


class LicenseShortCut(TypedDict):
    """Shortcut to add a copyright statement"""

    #: The copyright statement
    copyright: str

    #: year of copyright statement
    year: str

    #: SPDX Identifier of the license
    license: Optional[str]


def load_shortcuts() -> Dict[str, LicenseShortCut]:
    """Load the ``shortcuts.yaml`` file."""

    with open(osp.join(osp.dirname(__file__), "shortcuts.yaml")) as f:
        return yaml.safe_load(f)


def add_arguments(
    parser: ArgumentParser, shortcuts: Dict[str, LicenseShortCut]
):
    parser.add_argument(
        "shortcut",
        choices=[key for key in shortcuts if not key.startswith(".")],
        help=(
            "What license should be applied? Shortcuts are loaded from "
            ".reuse/shortcuts.yaml. Possible shortcuts are %(choices)s"
        ),
    )

    _orig_add_arguments(parser)

    parser.set_defaults(func=run)
    parser.set_defaults(parser=parser)


def main(argv=None):
    shortcuts = load_shortcuts()

    parser = ArgumentParser(
        prog=".reuse/add_license.py",
        description=dedent(
            """
            Add copyright and licensing into the header of files with shortcuts

            This script uses the ``reuse annotate`` command to add copyright
            and licensing information into the header the specified files.

            It accepts the same arguments as ``reuse annotate``, plus an
            additional required `shortcuts` argument. The given `shortcut`
            comes from the file at ``.reuse/shortcuts.yaml`` to fill in
            copyright, year and license identifier.

            For further information, please type ``reuse annotate --help``"""
        ),
    )
    add_arguments(parser, shortcuts)

    args = parser.parse_args(argv)

    shortcut = shortcuts[args.shortcut]

    if args.year is None:
        args.year = []
    if args.copyright is None:
        args.copyright = []

    if args.license is None and shortcut.get("license"):
        args.license = [shortcut["license"]]
    elif args.license and shortcut.get("license"):
        args.license.append(shortcut["license"])
    args.year.append(shortcut["year"])
    args.copyright.append(shortcut["copyright"])

    project = Project(find_root())
    args.func(args, project)


if __name__ == "__main__":
    main()
