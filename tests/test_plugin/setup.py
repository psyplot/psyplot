from setuptools import find_packages, setup

# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht

# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

setup(
    name="psyplot_test",
    version="1.0.0",
    license="GPLv2",
    packages=find_packages(exclude=["docs", "tests*", "examples"]),
    entry_points={
        "psyplot": [
            "plugin=psyplot_test.plugin",
            "patches=psyplot_test.plugin:patches",
        ]
    },
    zip_safe=False,
)
