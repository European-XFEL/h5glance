#compdef _h5glance h5glance

function _h5glance {
    local curcontext="$curcontext"
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \
        "-h[Show help information]" \
        "--help[Show help information]" \
        "--version[Show version number]" \
        "--attrs[Show attributes of groups]" \
        ":HDF5 file:_files" \
        ":path in file:->infile"

    case "$state" in
        infile)
                declare -a matches
                local grouppath=""
                if [[ ${line[2]} =~ / ]]; then
                  # Hack: 'dirname a/b/' returns 'a'. The trailing x makes it 'a/b'.
                  grouppath=$(dirname "${line[2]}x")/
                fi

                # List entries in the group, add the group path and a / suffix for
                # subgroups, and case-insensitively filter them against the text entered.
                matches=($(h5ls --simple "${line[1]}/${grouppath}" \
                          | awk -v g="${grouppath}" \
                              '{s=""; if ($2 == "Group") s="/"; print g $1 s}' \
                          | awk -v IGNORECASE=1 -v p="${line[2]}" \
                              'p==substr($0,0,length(p))' ))

                # Code below by Xavier Delaruelle, on StackOverflow.
                # https://stackoverflow.com/a/53907053/434217
                # Used under SO's default CC-BY-SA-3.0 license.
                local suffix=' ';
                # do not append space to word completed if it is a directory (ends with /)
                for val in $matches; do
                        if [ "${val: -1:1}" = '/' ]; then
                            suffix=''
                            break
                        fi
                done

                # The -M match-spec argument allows case-insensitive matches
                compadd -S "$suffix" -M 'm:{a-zA-Z}={A-Za-z}' -a matches
                ;;
    esac
}
