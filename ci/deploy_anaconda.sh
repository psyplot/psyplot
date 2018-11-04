#!/bin/bash
anaconda -t $CONDA_REPO_TOKEN upload -l $TRAVIS_BRANCH --force "$(ls $HOME/miniconda/conda-bld/${TRAVIS_OS_NAME}-64/*.tar.bz2)"
