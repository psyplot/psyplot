#!/usr/bin/env python
import os
import re
import conda_build.api
import subprocess as spr
fnames = list(conda_build.api.get_output_file_paths('conda-recipe'))
py_patt = re.compile('py\d\d')
repl = 'py' + os.getenv('PYTHON_VERSION').replace('.', '')
fnames = [py_patt.sub(repl, f) for f in fnames]
if os.getenv("TRAVIS") == "true":
    branch = os.getenv("TRAVIS_BRANCH")
    on_release = os.getenv("TRAVIS_TAG") != ""
else:
    branch = os.getenv("APPVEYOR_REPO_BRANCH")
    on_release = bool(os.getenv("APPVEYOR_REPO_TAG_NAME"))
label = ['-l', branch] if not on_release else []
token = ['-t', os.getenv('CONDA_REPO_TOKEN')]

print("Uploading via " +
      " ".join(['anaconda -t *****', 'upload', '--force'] + label + fnames))

spr.check_call(
    ['anaconda'] + token + ['upload', '--force'] +
    label + fnames
)
