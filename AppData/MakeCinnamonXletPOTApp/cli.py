#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Main command line application.

Attributes
----------
docopt_doc : str
    Used to store/define the docstring that will be passed to docopt as the "doc" argument.
root_folder : str
    The main folder containing the application. All commands must be executed from this location
    without exceptions.
"""

import os
import sys

from . import app_utils
from .__init__ import __appname__, __appdescription__, __version__, __status__
from .python_utils import exceptions, log_system, shell_utils, file_utils
from .python_utils.docopt import docopt

if sys.version_info < (3, 5):
    raise exceptions.WrongPythonVersion()

root_folder = os.path.realpath(os.path.abspath(os.path.join(
    os.path.normpath(os.getcwd()))))

# Store the "docopt" document in a variable to SHUT THE HELL UP Sphinx.
docopt_doc = """{__appname__} {__version__} {__status__}

{__appdescription__}

Usage:
    app.py [-j | --skip-js] [-p | --skip-python]
           [-o <path> | --output=<path>]
           [-c | --custom-header]
           [-a <path>... | --scan-additional-file=<path>...]
           [-s <key>... | --skip-key=<key>...]
           [-k <keyword>... | --keyword=<keyword>...]
           [-g <pattern>... | --ignored-pattern=<pattern>...]
           [-x <path> | --xlet-dir=<path>]
    app.py (-i | --install | -r | --remove)
           [-x <path> | --xlet-dir=<path>]
    app.py generate system_executable
    app.py (-h | --help | --version)

Options:

-h, --help
    Show this screen.

--version
    Show application version.

-j, --skip-js
    Do not scan JavaScript files inside the xlet folder for translatable
    strings.

-p, --skip-python
    Do not scan Python files inside the xlet folder for translatable strings.

-k <keyword>, --keyword=<keyword>
    Assign one or more keywords to be passed to the xgettext command.
    If none is passed, the "_" keyword will be used. Specifying this option
    will override the default one ("_"). If "_" is intended to also be used in
    addition to a new keyword, "_" should also be passed.

-g <pattern>, --ignored-pattern=<pattern>
    A list of file/folder names patterns (in glob-style) to ignore when
    scanning an xlet directory.

-o <path>, --output=<path>
    Use this option to specify the location where to store the generated .pot
    file. By default <uuid>/po/<uuid>.pot is used.

-c, --custom-header
    Modify the .pot file header with custom data. The data will be extracted
    from a file named exactly <uuid>.pot that should be placed inside an xlet
    "po" folder.

-a <path>, --scan-additional-file=<path>
    Specify additional files to scan that are outside the xlet folder.
    Can be full paths or relative (to the xlet folder) paths.
    Only JavaScript and Python files can be specified and they all should
    have their file extension specified (.js or .py).
    Warning!!! Absolute paths will be displayed as-is inside the
    generated POT file comments.

-s <key>, --skip-key=<key>
    A preference key as found inside the settings-schema.json file to be
    ignored by the strings extractor.

-x <path>, --xlet-dir=<path>
    The path to the xlet directory. If not specified, the current working
    directory will be used.

-i, --install
    Compiles and installs any .po files contained inside an xlet "po" folder
    to the system locale store. The xlet UUID will be used as the
    translation domain.

-r, --remove
    The opposite of install, removes translations from the system locale store.
    Again, the xlet UUID will be used to find the correct files to remove.

""".format(__appname__=__appname__,
           __appdescription__=__appdescription__,
           __version__=__version__,
           __status__=__status__)


class CommandLineTool():
    """Command line tool.

    It handles the arguments parsed by the docopt module.

    Attributes
    ----------
    action : method
        Set the method that will be executed when calling CommandLineTool.run().
    args : dict
        The dictionary of arguments as returned by docopt parser.
    logger : object
        See <class :any:`LogSystem`>.
    """

    def __init__(self, args):
        """
        Parameters
        ----------
        args : dict
            The dictionary of arguments as returned by docopt parser.
        """
        super(CommandLineTool, self).__init__()

        self.args = args
        self.action = None
        logs_storage_dir = "UserData/logs"
        log_file = log_system.get_log_file(storage_dir=logs_storage_dir,
                                           prefix="CLI")
        file_utils.remove_surplus_files(logs_storage_dir, "CLI*")
        self.logger = log_system.LogSystem(filename=log_file,
                                           verbose=True)

        self.logger.info(shell_utils.get_cli_header(__appname__), date=False)
        print("")

        if args["generate"]:
            if args["system_executable"]:
                self.logger.info("System executable generation...")
                self.action = self.system_executable_generation
        else:
            self.action = self.scan_xlet

    def run(self):
        """Execute the assigned action stored in self.action if any.
        """
        if self.action is not None:
            self.action()

    def scan_xlet(self):
        """See :any:`app_utils.scan_xlet`
        """
        app_utils.scan_xlet(self.args, self.logger)

    def system_executable_generation(self):
        """See :any:`template_utils.system_executable_generation`
        """
        from .python_utils import template_utils

        template_utils.system_executable_generation(
            exec_name="make-cinnamon-xlet-pot-cli",
            app_root_folder=root_folder,
            sys_exec_template_path=os.path.join(
                root_folder, "AppData", "data", "templates", "system_executable"),
            bash_completions_template_path=os.path.join(
                root_folder, "AppData", "data", "templates", "bash_completions.bash"),
            logger=self.logger
        )


def main():
    """Initialize main command line interface.

    Raises
    ------
    exceptions.BadExecutionLocation
        Do not allow to run any command if the "flag" file isn't
        found where it should be. See :any:`exceptions.BadExecutionLocation`.
    """
    if not os.path.exists(".make-cinnamon-xlet-pot.flag"):
        raise exceptions.BadExecutionLocation()

    arguments = docopt(docopt_doc, version="%s %s %s" % (__appname__, __version__, __status__))
    cli = CommandLineTool(arguments)
    cli.run()


if __name__ == "__main__":
    pass
