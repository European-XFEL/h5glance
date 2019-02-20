#!/usr/bin/env bash

_h5glance()
{
    local cur prev opts base
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Complete options
    if [[ ${cur} = -* ]]; then
      opts="-h --help --version --attrs"
      COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
      return 0
    fi

    # Complete paths inside file
    if [[ -f ${prev} ]]; then
      COMPREPLY=( $(_h5glance_complete_infile "${prev}" "${cur}") )
      return 0
    fi
}

complete -o default -o nospace -F _h5glance h5glance
