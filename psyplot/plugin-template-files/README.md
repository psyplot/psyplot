# PLUGIN_NAME: PLUGIN_DESC

This template serves as a basis for new psyplot plugins. Go through every file
and adapt it to your needs. A small overview on the important files in this
package:

- setup.py: The installation script
- PLUGIN_PYNAME/plugin.py: The plugin module that is imported at startup of
  psyplot
- PLUGIN_PYNAME/plotters.py: The module that defines the plotters for the plugin
- COPYING and COPYING.LESSER: The license file of your package (uses LGPL-3.0
  but you can change this)

Of course you can change the names of these files to anything you want. Just
make sure that they are correctly specified in the install script.
