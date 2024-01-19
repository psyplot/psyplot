"""Create the psyplot icon.

This script creates the psyplot icon with a dpi of 128 and a width and height
of 8 inches. The file is saved it to ``'icon1024.pkl'``"""

# SPDX-FileCopyrightText: 2016-2024 University of Lausanne
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht

# SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: LGPL-3.0-only

import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
from matplotlib.text import FontProperties

# The path to the font
fontpath = "/Library/Fonts/FreeSansBoldOblique.ttf"

fig = plt.figure(figsize=(8, 8), dpi=128)

ax = fig.add_axes(
    [0.0, 0.0, 1.0, 1.0], projection=ccrs.Orthographic(central_latitude=5)
)

land = ax.add_feature(cf.LAND, facecolor="0.975")
ocean = ax.add_feature(cf.OCEAN, facecolor=plt.get_cmap("Blues")(0.5))

text = ax.text(
    0.47,
    0.5,
    "Psy",
    transform=fig.transFigure,
    name="FreeSans",
    fontproperties=FontProperties(fname=fontpath),
    size=256,
    ha="center",
    va="center",
    weight=400,
)

ax.outline_patch.set_edgecolor("none")

plt.savefig("icon1024.png", transparent=True)
