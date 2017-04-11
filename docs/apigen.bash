#!/bin/bash
# script to automatically generate the psyplot api documentation using
# sphinx-apidoc and sed
sphinx-apidoc -f -M -e  -T -o api ../psyplot/ 
# replace chapter title in psyplot.rst
sed -i -e 1,1s/.*/'API Reference'/ api/psyplot.rst
# add imported members at the top level module
sed -i -e /Subpackages/'i\'$'\n'".. autosummary:: \\
\    ~psyplot.config.rcsetup.rcParams \\
\    ~psyplot.data.InteractiveArray \\
\    ~psyplot.data.InteractiveList \\
    \\
    " api/psyplot.rst

sphinx-autogen -o generated *.rst */*.rst

