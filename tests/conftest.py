"""pytest configuration file."""

# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht

# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only


def pytest_addoption(parser):
    group = parser.getgroup("psyplot", "psyplot specific options")
    group.addoption(
        "--no-removal",
        help="Do not remove created test files",
        action="store_true",
    )


def pytest_configure(config):
    if config.getoption("no_removal"):
        import test_project

        test_project.remove_temp_files = False
        import test_main

        test_main.remove_temp_files = False
