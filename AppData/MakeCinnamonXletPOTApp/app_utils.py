#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Application utilities.

Attributes
----------
LOCALE_DIR : str
    System's localizations storage for the current user.
POT_HEADER : str
    POT file header template.
root_folder : str
    The main folder containing the Knowledge Base. All commands must be executed
    from this location without exceptions.
"""

import datetime
import json
import os
import time

from collections import OrderedDict
from shutil import copy2
from shutil import ignore_patterns
from shutil import rmtree


from .__init__ import __version__
from .python_utils import cmd_utils
from .python_utils import exceptions
from .python_utils import file_utils
from .python_utils import misc_utils
from .python_utils import polib


root_folder = os.path.realpath(os.path.abspath(os.path.join(
    os.path.normpath(os.getcwd()))))

LOCALE_DIR = os.path.join(os.path.expanduser("~"), ".local/share/locale")

POT_HEADER = """# This is a template file for translating the {PACKAGE} package.
# Copyright (C) {COPY_INITIAL_YEAR}{COPY_CURRENT_YEAR}
# This file is distributed under the same license as the {PACKAGE} package.
# {FIRST_AUTHOR} {FIRST_AUTHOR_EMAIL}, {COPY_INITIAL_YEAR}{COPY_CURRENT_YEAR}.
#
msgid ""
msgstr ""
"Project-Id-Version: {PACKAGE} {VERSION}\\n"
"POT-Creation-Date: {TIMESTAMP}\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Generated-By: Make Cinnamon Xlet POT {SCRIPT_VERSION}\\n"
"""


def _get_time_zone():
    """Get time zone.

    Returns
    -------
    str
        Time zone.
    """
    if time.localtime().tm_isdst and time.daylight:
        tzone = -time.altzone
    else:
        tzone = -time.timezone

    # Up to here, tzone is an integer.
    tzone = str(tzone / 60 / 60)

    # And the ugliness begins!!!
    [h, m] = tzone.split(".")

    isNegative = int(h) < 0
    hours = "{0:03d}".format(int(h)) if isNegative else "{0:02d}".format(int(h))
    minutes = "{0:02d}".format(int(m))

    try:
        return (hours if isNegative else "+" + hours) + minutes
    except Exception:
        return "+0000"


def _get_timestamp():
    """Returns a time stamp in the same format used by xgettex.

    Returns
    -------
    str
        Time stamp.
    """
    now = datetime.datetime.now()
    # Since the "padding" with zeroes of the rest of the values converts
    # them into strings, lets convert to string the year too.
    YEAR = str(now.year)
    # "Pad" all the following values with zeroes.
    MO = "{0:02d}".format(now.month)
    DA = "{0:02d}".format(now.day)
    HO = "{0:02d}".format(now.hour)
    MI = "{0:02d}".format(now.minute)
    ZONE = _get_time_zone()

    return "%s-%s-%s %s:%s%s" % (YEAR, MO, DA, HO, MI, ZONE)


def _scan_json(xlet_dir, pot_path, ignored_keys=[]):
    """Scan the settings-schema.json and metadata.json files.

    Parameters
    ----------
    xlet_dir : str
        The xlet root directory.
    pot_path : str
        The path to the POT file.
    ignored_keys : list
        List of keys to ignore from the string extraction.
    """
    append = os.path.exists(pot_path)

    if append:
        pot_file = polib.pofile(pot_path, encoding="UTF-8",
                                check_for_duplicates=True, wrapwidth=99999999)
    else:
        pot_file = polib.POFile()

    for root, dirs, files in os.walk(xlet_dir):
        dirs.sort()
        files.sort()
        rel_root = os.path.relpath(root)
        for file in files:
            if os.path.islink(os.path.join(root, file)):
                continue

            data = None

            if rel_root == ".":
                rel_path = file
            else:
                rel_path = os.path.join(rel_root, file)

            if file == "settings-schema.json":
                with open(os.path.join(root, file), "r", encoding="UTF-8") as settings_schema_file:
                    data = json.load(settings_schema_file,
                                     object_pairs_hook=OrderedDict)

                if data:
                    _extract_settings_strings(data, rel_path.replace(
                        "/", "->"), pot_file, ignored_keys=ignored_keys)
            elif file == "metadata.json":
                with open(os.path.join(root, file), "r", encoding="UTF-8") as metadata_file:
                    data = json.load(metadata_file, object_pairs_hook=OrderedDict)

                if data:
                    _extract_metadata_strings(data, rel_path.replace("/", "->"), pot_file)

    if append:
        pot_file.save()
    else:
        pot_file.save(fpath=pot_path)


def _extract_settings_strings(data, rel_path, pot_file, parent="", ignored_keys=[]):
    """Extract data from the settings-schema.json file.

    Parameters
    ----------
    data : dict
        Dictionary from which to extract strings.
    rel_path : str
        Relative path used to generate a comment for a POT entry.
    pot_file : <class "polib.POFile">
        The "polib.POFile" object to work with.
    parent : str, optional
        A key name of the "data" dictionary to insert into the comment for a POT entry.
    ignored_keys : list, optional
        List of keys to ignore from the string extraction.
    """
    for key in data.keys():
        if key in ignored_keys:
            logger.info("**Key <%s> ignored.**" % key, date=False)
            continue

        if key in ("description", "tooltip", "units", "title"):
            comment = "%s->%s->%s" % (rel_path, parent, key)
            _save_entry(data[key], comment, pot_file)
        elif key == "options":
            opt_data = data[key]

            for option in opt_data.keys():
                if opt_data[option] == "custom":
                    continue

                comment = "%s->%s->%s" % (rel_path, parent, key)
                _save_entry(option, comment, pot_file)
        elif key == "columns":
            columns = data[key]

            for i, col in enumerate(columns):
                for col_key in col:
                    if col_key in ("title", "units"):
                        comment = "%s->%s->columns->%s" % (rel_path, parent, col_key)
                        _save_entry(col[col_key], comment, pot_file)

        try:
            _extract_settings_strings(data[key], rel_path, pot_file, key, ignored_keys)
        except AttributeError:
            pass


def _extract_metadata_strings(data, rel_path, pot_file):
    """Extract data from the metadata.json file.

    Parameters
    ----------
    data : dict
        Dictionary from which to extract strings.
    rel_path : str
        Relative path used to generate a comment for a POT entry.
    pot_file : <class "polib.POFile">
        The "polib.POFile" object to work with.
    """
    for key in data:
        if key in ("name", "description", "comments"):
            comment = "%s->%s" % (rel_path, key)
            _save_entry(data[key], comment, pot_file)
        elif key == "contributors":
            comment = "%s->%s" % (rel_path, key)
            values = data[key]

            if isinstance(values, str):
                values = values.split(",")

            for value in values:
                _save_entry(value.strip(), comment, pot_file)


def _save_entry(msgid, comment, pot_file):
    """Save entry.

    Parameters
    ----------
    msgid : str
        The string that will be saved into the POT file.
    comment : str
        The comment for the msgid.
    pot_file : str
        The "polib.POFile" object to work with.

    Returns
    -------
    None
        Halt function execution.
    """
    if not msgid.strip():
        return

    entry = pot_file.find(msgid)

    if entry:
        if comment not in entry.comment:
            if entry.comment:
                entry.comment += "\n"
            entry.comment += comment
    else:
        entry = polib.POEntry(msgid=msgid, comment=comment)
        pot_file.append(entry)


def _remove_empty_folders(path):
    """Remove empty folders when removing an xlet localizations.

    Parameters
    ----------
    path : str
        Path to the installed xlet localizations.

    Returns
    -------
    None
        Halt function execution.
    """
    if not os.path.isdir(path):
        return

    # Remove empty sub-folders.
    files = os.listdir(path)

    if len(files):
        for f in files:
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath):
                _remove_empty_folders(fullpath)

    # If folder empty, delete it.
    files = os.listdir(path)

    if len(files) == 0:
        logger.info("**Removing empty folder:** %s" % path, date=False)
        os.rmdir(path)


def _do_install(uuid, xlet_dir):
    """Install xlet's localizations.

    Parameters
    ----------
    uuid : str
        The UUID of the xlet to install.
    xlet_dir : str
        The xlet root directory.

    Raises
    ------
    exceptions.WrongExecutionLocation
        Wrong execution location.
    """
    podir = os.path.join(xlet_dir, "po")
    files_installed = 0

    if not os.path.exists(podir):
        msg = [
            "The 'po' directory seems not to be present.",
            "This xlet might not have localizations that need to be installed.",
            "Or this tool has not been executed from inside the xlet folder."
        ]
        raise exceptions.WrongExecutionLocation("\n".join(msg))

    for root, dirs, files in os.walk(podir):
        for file in files:
            locale_name, ext = os.path.splitext(file)
            if ext == ".po":
                lang_locale_dir = os.path.join(LOCALE_DIR, locale_name, "LC_MESSAGES")
                os.makedirs(lang_locale_dir, mode=0o755, exist_ok=True)
                cmd_utils.run_cmd(["msgfmt", "-c", os.path.join(root, file), "-o",
                                   os.path.join(lang_locale_dir, "%s.mo" % uuid)])
                files_installed += 1

    if files_installed == 0:
        logger.info("**Nothing to install.**", date=False)
    else:
        logger.info("**Installed %i files.**" % files_installed, date=False)


def _do_remove(uuid):
    """Remove xlet's localizations.

    Parameters
    ----------
    uuid : str
        The UUID of the xlet to remove.
    """
    files_removed = 0

    if (os.path.exists(LOCALE_DIR)):
        locale_names = os.listdir(LOCALE_DIR)
        for locale_name in locale_names:
            lang_locale_dir = os.path.join(LOCALE_DIR, locale_name)
            mo_file = os.path.join(lang_locale_dir, "LC_MESSAGES", "%s.mo" % uuid)
            if os.path.isfile(mo_file):
                os.remove(mo_file)
                files_removed += 1
            _remove_empty_folders(lang_locale_dir)

    if files_removed == 0:
        logger.info("**Nothing to remove.**", date=False)
    else:
        logger.info("**Removed %i files.**" % files_removed, date=False)


def _insert_custom_header(xlet_dir, pot_path, pot_settings_data):
    """Insert custom header.

    Parameters
    ----------
    xlet_dir : str
        The xlet root directory.
    pot_path : str
        The path to the POT file.
    pot_settings_data : dict
        Extra settings found inside the JSON file next to the generated POT file.

    Raises
    ------
    SystemExit
        Quit program.
    """
    metadata = None

    try:
        with open(os.path.join(xlet_dir, "metadata.json"), "r", encoding="UTF-8") as md_file:
            raw_meta = md_file.read()

        md = json.loads(raw_meta)

        metadata = {
            "FIRST_AUTHOR": "FIRST_AUTHOR",
            "FIRST_AUTHOR_EMAIL": "<EMAIL@ADDRESS>",
            "COPY_INITIAL_YEAR": "",
            "COPY_CURRENT_YEAR": str(datetime.datetime.now().year),
            "PACKAGE": os.path.basename(xlet_dir),
            "VERSION": md.get("version", "VERSION"),
            "SCRIPT_VERSION": __version__,
            "TIMESTAMP": _get_timestamp(),
        }
    except Exception as detail:
        logger.error(detail)
        raise SystemExit(
            "Failed to get metadata - missing, corrupt, or incomplete metadata.json file.")

    if metadata is None:
        raise SystemExit()

    try:
        if pot_settings_data is not None:
            current_year = metadata["COPY_CURRENT_YEAR"]
            copy_initial_year = pot_settings_data.get("COPY_INITIAL_YEAR", "")

            if copy_initial_year:
                if copy_initial_year != current_year:
                    copy_initial_year = copy_initial_year + "-"
                elif copy_initial_year == current_year:
                    copy_initial_year = ""

            metadata["COPY_INITIAL_YEAR"] = copy_initial_year
            metadata["FIRST_AUTHOR"] = pot_settings_data.get("FIRST_AUTHOR", "FIRST_AUTHOR")
            metadata["FIRST_AUTHOR_EMAIL"] = pot_settings_data.get(
                "FIRST_AUTHOR_EMAIL", "<EMAIL@ADDRESS>")
    except Exception:
        pass

    try:
        with open(pot_path, "r", encoding="UTF-8") as pot_file:
            raw_data = pot_file.readlines()

        new_header = POT_HEADER.format(
            FIRST_AUTHOR=metadata["FIRST_AUTHOR"],
            FIRST_AUTHOR_EMAIL=metadata["FIRST_AUTHOR_EMAIL"],
            COPY_CURRENT_YEAR=metadata["COPY_CURRENT_YEAR"],
            COPY_INITIAL_YEAR=metadata["COPY_INITIAL_YEAR"],
            PACKAGE=metadata["PACKAGE"],
            VERSION=metadata["VERSION"],
            SCRIPT_VERSION=metadata["SCRIPT_VERSION"],
            TIMESTAMP=metadata["TIMESTAMP"]
        )

        with open(pot_path, "w", encoding="UTF-8") as pot_file:
            raw_data_no_header = "".join(raw_data[raw_data.index("\n"):])
            pot_file.write(new_header + raw_data_no_header)
    except Exception as detail:
        logger.error(detail)
        raise SystemExit("Failed to set custom header.")

    logger.info("**POT header customization complete.**", date=False)


def _generate_trans_stats(uuid, xlet_dir, pot_path):
    """Generate translations statistics.

    Generates files that contain the amount of untranslated strings an xlet has.

    Raises
    ------
    SystemExit
        Halt execution if the msgmerge command is not found.

    Parameters
    ----------
    uuid : str
        An xlet UUID.
    xlet_dir : str
        Path to an xlet folder.
    pot_path : str
        Path to a POT file.
    """
    if not cmd_utils.which("msgmerge"):
        logger.error("**MissingCommand:** msgmerge command not found!!!")
        raise SystemExit(1)

    markdown_content = []
    po_tmp_storage = os.path.join(misc_utils.get_system_tempdir(),
                                  "MakeCinnamonXletPOT-tmp", uuid)
    trans_stats_file = os.path.join(po_tmp_storage, "po_files_untranslated_table.md")
    rmtree(po_tmp_storage, ignore_errors=True)
    os.makedirs(po_tmp_storage, exist_ok=True)

    xlet_po_dir = os.path.join(xlet_dir, "po")
    tmp_xlet_po_dir = os.path.join(po_tmp_storage, "po")
    os.makedirs(tmp_xlet_po_dir, exist_ok=True)

    if file_utils.is_real_dir(xlet_po_dir):
        xlet_po_list = file_utils.recursive_glob(xlet_po_dir, "*.po")

        if xlet_po_list:
            logger.info(uuid, date=False)
            markdown_content = [
                "### %s" % uuid,
                "",
                "|LANGUAGE|UNTRANSLATED|",
                "|--------|------------|",
            ]

            for po_file_path in xlet_po_list:
                po_base_name = os.path.basename(po_file_path)
                tmp_po_file_path = os.path.join(tmp_xlet_po_dir, po_base_name)

                logger.info("**Copying %s to temporary location...**" %
                            po_base_name, date=False)
                copy2(po_file_path, tmp_po_file_path)

                logger.info("**Updating temporary %s from localization template...**" %
                            po_base_name, date=False)
                cmd_utils.run_cmd([
                    "msgmerge",
                    "--silent",             # Shut the heck up.
                    "--no-wrap",            # Do not wrap long lines.
                    "--no-fuzzy-matching",  # Do not use fuzzy matching.
                    "--backup=off",         # Never make backups.
                    "--update",             # Update .po file, do nothing if up to date.
                    tmp_po_file_path,       # The .po file to update.
                    pot_path                # The template file to update from.
                ], stdout=None, stderr=None)

                logger.info("**Counting untranslated strings...**", date=False)
                trans_count_cmd = 'msggrep -v -T -e "." "%s" | grep -c ^msgstr'
                trans_count_output = cmd_utils.run_cmd(trans_count_cmd % tmp_po_file_path,
                                                       shell=True).stdout
                trans_count = int(trans_count_output.decode("UTF-8").strip())
                markdown_content.append("|%s|%d|" % (
                    po_base_name, trans_count - 1 if trans_count > 0 else trans_count))

    if markdown_content:
        with open(trans_stats_file, "w", encoding="UTF-8") as trans_file:
            trans_file.write("\n".join(markdown_content))

        cmd_utils.run_cmd(["xdg-open", trans_stats_file])


def scan_xlet(args, app_logger):
    """Scan xlet.

    Raises
    ------
    exceptions.MissingCommand
        See <class :any:`exceptions.MissingCommand`>.
    SystemExit
        Quit program.

    Parameters
    ----------
    args : list
        The list of arguments passed by the CLI application.
    app_logger : object
        See <class :any:`LogSystem`>.
    """
    global logger
    logger = app_logger

    # NOTE: list(set()) is cast to workaround docopt bug that duplicates arguments.
    keywords = list(set(args["--keyword"])) if args["--keyword"] else ["_"]
    ignored_patterns = list(set(args["--ignored-pattern"]))
    additional_files = list(set(args["--scan-additional-file"]))
    skip_keys = list(set(args["--skip-key"]))

    xlet_dir = os.path.abspath(args["--xlet-dir"])

    if not os.path.exists(xlet_dir):
        raise SystemExit("%s does not exist." % xlet_dir)

    uuid = os.path.basename(xlet_dir)

    logger.info("**Xlet: %s**" % uuid, date=False)

    if args["--output"]:
        pot_path = os.path.abspath(args["--output"])
        pot_options_path = pot_path[:-4] + ".json"
    else:
        pot_path = os.path.join(xlet_dir, "po", uuid + ".pot")
        pot_options_path = os.path.join(xlet_dir, "po", uuid + ".json")

    if args["--gen-stats"]:
        pot_path = args["--pot-file"] if args["--pot-file"] else pot_path
        raise SystemExit(_generate_trans_stats(uuid, xlet_dir, pot_path))

    if args["--install"]:
        raise SystemExit(_do_install(uuid, xlet_dir))

    if args["--remove"]:
        raise SystemExit(_do_remove(uuid))

    # NOTE: From this point down, all actions are to generate a new POT file.

    # Remove an existent POT file. This is to force `xgettext` to always create a new POT file.
    # `xgettext` doesn't remove obsolete strings from existent POT files and it doesn't update
    # the line reference from a msgid whose source code has been moved.
    if os.path.exists(pot_path):
        os.remove(pot_path)

    pwd = os.getcwd()
    os.chdir(xlet_dir)

    # NOTE: To future me to avoid headaches and nightmares!!!
    #
    # 1. Create the po directory. Otherwise, the polib module will fail if there isn't an
    #    existent POT file when calling its `potfile.save()` method.
    # 2. Run xgettext commands (to scan JavaScript and Python files) BEFORE running the _scan_json
    #    function using polib. Because:
    #    - Running polib before xgettext will generate POT files with double headers. ¬¬
    #    - Running polib before xgettext with --omit-header fixes the double headers problem, but
    #      the absolutely retarded xgettext will f*ck up all unicode characters.

    os.makedirs(os.path.dirname(pot_path), mode=0o755, exist_ok=True)

    if not args["--skip-js"] or not args["--skip-python"]:
        if not cmd_utils.which("xgettext"):
            raise exceptions.MissingCommand(
                "xgettext command not found, you may need to install the gettext package.")

        xgettext_command = ["xgettext"] + ["--keyword=" + item for item in keywords] + [
            "--no-wrap",
            "--sort-by-file",
            "--add-comments",
            "--from-code=UTF-8",
            "--output=%s" % pot_path
        ]

    if not args["--skip-js"]:
        logger.info("**Scanning JavaScript files...**", date=False)

        js_files = []

        if additional_files:
            for file in additional_files:
                if file[-3:] == ".js":
                    js_files.append(file)

            if len(js_files) > 0:
                logger.info("**Including the following additional JavaScript file/s...**", date=False)

                for f in js_files:
                    logger.info(f, date=False)

        for root, dirs, files in os.walk(xlet_dir):
            dirs.sort()
            rel_root = os.path.relpath(root)
            for file in files:
                if file[-3:] == ".js":
                    js_files.append(os.path.join(rel_root, file))

        if len(js_files) == 0:
            logger.info("**No JavaScript files found.**", date=False)
        else:
            if ignored_patterns:
                ignored_js_files = ignore_patterns(*ignored_patterns)(None, js_files)
                js_files = [file for file in js_files if file not in ignored_js_files]

            logger.info("**Found %i JavaScript file(s)**" % len(js_files), date=False)

            if os.path.exists(pot_path):
                xgettext_command.append("--join-existing")

            cmd_utils.run_cmd(xgettext_command + ["--language=JavaScript"] + sorted(js_files))

    if not args["--skip-python"]:
        logger.info("**Scanning Python files...**", date=False)

        py_files = []

        if additional_files:
            for file in additional_files:
                if file[-3:] == ".py":
                    py_files.append(file)

            if len(py_files) > 0:
                logger.info("**Including the following additional Python file/s...**", date=False)

                for f in py_files:
                    logger.info(f, date=False)

        for root, dirs, files in os.walk(xlet_dir):
            dirs.sort()
            rel_root = os.path.relpath(root)
            for file in files:
                if file[-3:] == ".py":
                    py_files.append(os.path.join(rel_root, file))

        if len(py_files) == 0:
            logger.info("**No Python files found.**", date=False)
        else:
            if ignored_patterns:
                ignored_py_files = ignore_patterns(*ignored_patterns)(None, py_files)
                py_files = [file for file in py_files if file not in ignored_py_files]

            logger.info("**Found %i Python file(s)**" % len(py_files), date=False)

            # Adding the --join-existing argument when there isn't a generated .pot file will
            # not save the strings extracted from Python files.
            # A .pot file might not be created if there isn't any translatable
            # string found inside the JavaScript files or if the --skip-js argument is used.
            if os.path.exists(pot_path):
                xgettext_command.append("--join-existing")

            cmd_utils.run_cmd(xgettext_command + ["--language=Python"] + sorted(py_files))

    pot_settings_data = None

    try:
        if os.path.exists(pot_options_path):
            with open(pot_options_path, "r", encoding="UTF-8") as pot_settings_file:
                raw_data = pot_settings_file.read()
                pot_settings_data = json.loads(raw_data)
    except Exception:
        pass

    ignored_keys = []

    if skip_keys:
        try:
            ignored_keys.extend(skip_keys)
        except Exception:
            ignored_keys = []

    if pot_settings_data is not None and "SKIP_KEYS" in pot_settings_data:
        ignored_keys.extend(pot_settings_data["SKIP_KEYS"])

    ignored_keys = list(set(ignored_keys))

    logger.info("**Scanning metadata.json and settings-schema.json files...**", date=False)
    _scan_json(xlet_dir, pot_path, ignored_keys)

    os.chdir(pwd)

    logger.info("**Extraction complete.**", date=False)

    if args["--custom-header"]:
        logger.info("**Customizing POT header...**", date=False)
        _insert_custom_header(xlet_dir, pot_path, pot_settings_data)

    raise SystemExit()


if __name__ == "__main__":
    pass
