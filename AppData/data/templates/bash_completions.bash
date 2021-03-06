#!/bin/bash

# It would have been impossible to create this without the following post on Stack Exchange!!!
# https://unix.stackexchange.com/a/55622

type "{executable_name}" &> /dev/null &&
_decide_nospace_{current_date}(){
    if [[ ${1} == "--"*"=" ]] ; then
        type "compopt" &> /dev/null && compopt -o nospace
    fi
} &&
__make_cinnamon_xlet_pot_cli_{current_date}(){
    local cur prev cmd main_options
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    main_options="-j --skip-js -p --skip-python -o --output= -c --custom-header \
-a --scan-additional-file= -s --skip-key= -k --keyword= -g --ignored-pattern= -x --xlet-dir= \
-i --install -r --remove -t --gen-stats generate -h --help --manual --version"

    # Handle --xxxxxx=
    if [[ ${prev} == "--"* && ${cur} == "=" ]] ; then
        type "compopt" &> /dev/null && compopt -o filenames
        COMPREPLY=(*)
        return 0
    fi

    # Handle --xxxxx=path
    case ${prev} in
        "="|"-o"|"-e")
            # Unescape space
            cur=${cur//\\ / }
            # Expand tilde to $HOME
            [[ ${cur} == "~/"* ]] && cur=${cur/\~/$HOME}
            # Show completion if path exist (and escape spaces)
            type "compopt" &> /dev/null && compopt -o filenames
            local files=("${cur}"*)
            [[ -e ${files[0]} ]] && COMPREPLY=( "${files[@]// /\ }" )
            return 0
        ;;
    esac

    # Completion of commands and "first level" options.
    if [[ $COMP_CWORD == 1 ]]; then
        COMPREPLY=( $(compgen -W "$main_options" -- "${cur}") )
        _decide_nospace_{current_date} ${COMPREPLY[0]}
    fi

    # Completion of options and sub-commands.
    cmd="${COMP_WORDS[1]}"

    case $cmd in
    "-i"|"--install"|"-r"|"--remove")
        COMPREPLY=( $(compgen -W "-x --xlet-dir=" -- "${cur}") )
        _decide_nospace_{current_date} ${COMPREPLY[0]}
        ;;
    "-t"|"--gen-stats")
        COMPREPLY=( $(compgen -W "-x --xlet-dir= -f --pot-file=" -- "${cur}") )
        _decide_nospace_{current_date} ${COMPREPLY[0]}
        ;;
    "generate")
        COMPREPLY=( $(compgen -W "system_executable" -- "${cur}") )
        ;;
    *)
        COMPREPLY=( $(compgen -W "$main_options" -- "${cur}") )
    ;;
    esac
} &&
complete -F __make_cinnamon_xlet_pot_cli_{current_date} {executable_name}
