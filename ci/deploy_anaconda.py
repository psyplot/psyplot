#!/usr/bin/env python
import os
import re
import conda_build.api
import subprocess as spr

recipe_path = 'ci/conda-recipe'

if os.getenv("TRAVIS") == "true":
    branch = os.getenv("TRAVIS_BRANCH")
    on_release = os.getenv("TRAVIS_TAG") != ""
else:
    branch = os.getenv("APPVEYOR_REPO_BRANCH")
    on_release = bool(os.getenv("APPVEYOR_REPO_TAG_NAME"))

label = ['--label', branch] if not on_release else []
token = ['--token', os.getenv('CONDA_REPO_TOKEN')]
python = ['--python', os.getenv('PYTHON_VERSION')]

command = ["conda", "build", "--no-test", "--no-copy-test-source-files"]

spr.check_call(["conda", "config", "--set", "anaconda_upload", "yes"])

print("Building recipe via " +
      " ".join(command + ["--token *******"] + label + python + [recipe_path]))

spr.check_call(command + token + label + python + [recipe_path])
