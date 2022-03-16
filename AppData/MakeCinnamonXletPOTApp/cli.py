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

from . import app_utils
from .__init__ import __appdescription__
from .__init__ import __appname__
from .__init__ import __status__
from .__init__ import __version__
from .python_utils import cli_utils

root_folder = os.path.realpath(os.path.abspath(os.path.join(
    os.path.normpath(os.getcwd()))))

docopt_doc = """{appname} {version} ({status})

{appdescription}

Usage:
    app.py (-h | --help | --manual | --version)
    app.py [-j | --skip-js] [-p | --skip-python]
           [-o <path> | --output=<path>]
           [-c | --custom-header]
           [-a <path>... | --scan-additional-file=<path>...]
           [-s <key>... | --skip-key=<key>...]
           [-k <keyword>... | --keyword=<keyword>...]
           [-g <pattern>... | --ignored-pattern=<pattern>...]
           [-x <path> | --xlet-dir=<path>]
    app.py (-i | --install | -r | --remove | -t | --gen-stats)
           [-x <path> | --xlet-dir=<path>]
           [-f <path> | --pot-file=<path>]
    app.py generate system_executable

Options:

-h, --help
    Show this screen.

--manual
    Show this application manual page.

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
    file. By default **<uuid>/po/<uuid>.pot** is used.

-c, --custom-header
    Modify the .pot file header with custom data. The data will be extracted
    from a file named exactly <uuid>.pot that should be placed inside an xlet
    **po** folder.

-a <path>, --scan-additional-file=<path>
    Specify additional files to scan that are outside the xlet folder.
    Can be full paths or relative (to the xlet folder) paths.
    Only JavaScript and Python files can be specified and they all should
    have their file extension specified (.js or .py).
    **Warning!!!** Absolute paths will be displayed as-is inside the
    generated POT file comments.

-s <key>, --skip-key=<key>
    A preference key as found inside the settings-schema.json file to be
    ignored by the strings extractor.

-x <path>, --xlet-dir=<path>
    The path to the xlet directory. If not specified, the current working
    directory will be used.

-f <path>, --pot-file=<path>
    The path to a POT file used to count untranslated strings when running the
    **--gen-stats** option. By default **<uuid>/po/<uuid>.pot** is used.

-i, --install
    Compiles and installs any .po files contained inside an xlet **po** folder
    to the system locale store. The xlet UUID will be used as the
    translation domain.

-r, --remove
    The opposite of install, removes translations from the system locale store.
    Again, the xlet UUID will be used to find the correct files to remove.

-t, --gen-stats
    Generate language statistics. It generates a table in Markdown format
    containg the number of untranslated strings for each .po file inside
    an xlet's **po** folder.

""".format(appname=__appname__,
           appdescription=__appdescription__,
           version=__version__,
           status=__status__)


class CommandLineInterface(cli_utils.CommandLineInterfaceSuper):
    """Command line interface.

    It handles the arguments parsed by the docopt module.

    Attributes
    ----------
    a : dict
        Where docopt_args is stored.
    action : method
        Set the method that will be executed when calling CommandLineTool.run().
    """
    action = None

    def __init__(self, docopt_args):
        """
        Parameters
        ----------
        docopt_args : dict
            The dictionary of arguments as returned by docopt parser.
        """
        self.a = docopt_args
        self._cli_header_blacklist = [self.a["--manual"]]

        super().__init__(__appname__)

        if self.a["--manual"]:
            self.action = self.display_manual_page
        elif self.a["generate"]:
            if self.a["system_executable"]:
                self.logger.info("**System executable generation...**")
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
        app_utils.scan_xlet(self.a, self.logger)

    def system_executable_generation(self):
        """See :any:`cli_utils.CommandLineInterfaceSuper._system_executable_generation`.
        """
        self._system_executable_generation(
            exec_name="make-cinnamon-xlet-pot-cli",
            app_root_folder=root_folder,
            sys_exec_template_path=os.path.join(
                root_folder, "AppData", "data", "templates", "system_executable"),
            bash_completions_template_path=os.path.join(
                root_folder, "AppData", "data", "templates", "bash_completions.bash"),
            logger=self.logger
        )

    def display_manual_page(self):
        """Display manual page.
        """
        from subprocess import call

        call(["man", "./app.py.1"], cwd=os.path.join(root_folder, "AppData", "data", "man"))


def main():
    """Initialize command line interface.
    """
    cli_utils.run_cli(flag_file=".make-cinnamon-xlet-pot.flag",
                      docopt_doc=docopt_doc,
                      app_name=__appname__,
                      app_version=__version__,
                      app_status=__status__,
                      cli_class=CommandLineInterface)


if __name__ == "__main__":
    pass
