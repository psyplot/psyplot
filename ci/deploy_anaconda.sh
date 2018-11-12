#!/bin/bash
if [[ $TRAVIS_TAG == "" ]]; then LABEL="-l $TRAVIS_BRANCH"; fi
anaconda -t $CONDA_REPO_TOKEN upload $LABEL --force "$(ls $HOME/miniconda/conda-bld/${TRAVIS_OS_NAME}-64/*.tar.bz2)"
