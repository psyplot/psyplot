# Create the iconset file for the psyplot icon.

# Disclaimer
# ----------
#
# Copyright (C) 2021 Helmholtz-Zentrum Hereon
# Copyright (C) 2020-2021 Helmholtz-Zentrum Geesthacht
# Copyright (C) 2016-2021 University of Lausanne
#
# This file is part of psyplot and is released under the GNU LGPL-3.O license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3.0 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU LGPL-3.0 license for more details.
#
# You should have received a copy of the GNU LGPL-3.0 license
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

mkdir main.iconset
sips -z 16 16     icon1024.png --out main.iconset/icon_16x16.png
sips -z 32 32     icon1024.png --out main.iconset/icon_16x16@2x.png
sips -z 32 32     icon1024.png --out main.iconset/icon_32x32.png
sips -z 64 64     icon1024.png --out main.iconset/icon_32x32@2x.png
sips -z 128 128   icon1024.png --out main.iconset/icon_128x128.png
sips -z 256 256   icon1024.png --out main.iconset/icon_128x128@2x.png
sips -z 256 256   icon1024.png --out main.iconset/icon_256x256.png
sips -z 512 512   icon1024.png --out main.iconset/icon_256x256@2x.png
sips -z 512 512   icon1024.png --out main.iconset/icon_512x512.png
cp icon1024.png main.iconset/icon_512x512@2x.png
iconutil -c icns main.iconset
rm -R main.iconset
