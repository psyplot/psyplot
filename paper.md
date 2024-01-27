<!--
SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH

SPDX-License-Identifier: CC-BY-4.0
-->

---
title: 'The psyplot interactive visualization framework'
tags:
  - visualization
  - netcdf
  - raster
  - cartopy
  - earth science
  - climate
  - matplotlib
  - python
authors:
 - name: Philipp S Sommer
   orcid: 0000-0001-6171-7716
   affiliation: 1
affiliations:
 - name: Institute of Earth Surface Dynamics, University of Lausanne, Géopolis, 1015 Lausanne, Switzerland
   index: 1
date: 28 July 2017
bibliography: paper.bib
---

# Summary

psyplot [@psyplot] is an cross-platform open source python project that mainly
combines the plotting utilities of matplotlib [@Hunter2007] and the data
management of the xarray [@hoyer2017xarray] package and integrates them into a
software that can be used via command-line and via a GUI.

The main purpose is to have a framework that allows a fast, attractive,
flexible, easily applicable, easily reproducible and especially an interactive
visualization of data.

The ultimate goal is to help scientists in their daily work by providing a
flexible visualization tool that can be enhanced by their own visualization
scripts.

The framework is extended by multiple plugins: psy-simple [@psy-simple] for
simple visualization tasks, psy-maps [@psy-maps] for georeferenced data
visualization and psy-reg [@psy-reg] for the visualization of fits. It is
furthermore extended by the optional graphical user interface psyplot-gui
[@psyplot-gui].

# References
