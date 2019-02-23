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
      local grouppath=""
      if [[ ${cur} =~ / ]]; then
        # Hack: 'dirname a/b/' returns 'a'. The trailing x makes it 'a/b'.
        grouppath=$(dirname "${cur}x")/
      fi

      # List entries in the group, add the group path and a / suffix for
      # subgroups, and case-insensitively filter them against the text entered.
      COMPREPLY=($(h5ls --simple "${prev}/${grouppath}" \
                  | awk -v g="${grouppath}" \
                      '{sfx=" "; if ($2 == "Group") sfx="/"; print g $1 sfx}' \
                  | awk -v IGNORECASE=1 -v p="${cur}" \
                      'p==substr($0,0,length(p))' \
                 ) )
      return 0
    fi
}

complete -o default -o nospace -F _h5glance h5glance
