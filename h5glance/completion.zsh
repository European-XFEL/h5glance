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
            declare -a matching_paths
            matching_paths=($(_h5glance_complete_infile "${line[1]}" "${line[2]}"))

            # Code below by Xavier Delaruelle, on StackOverflow.
            # https://stackoverflow.com/a/53907053/434217
            # Used under SO's default CC-BY-SA-3.0 license.
            local suffix=' ';
            # do not append space to word completed if it is a directory (ends with /)
            for val in $matching_paths; do
                    if [ "${val: -1:1}" = '/' ]; then
                        suffix=''
                        break
                    fi
            done

            # The -M match-spec argument allows case-insensitive matches
            compadd -S "$suffix" -M 'm:{a-zA-Z}={A-Za-z}' -a matching_paths
            ;;
    esac
}
