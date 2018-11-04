#!/bin/bash
anaconda -t $CONDA_REPO_TOKEN upload -l $TRAVIS_BRANCH --force $BUILDS
