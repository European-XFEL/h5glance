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
            # Case insensitive matching:
            zstyle ":completion::complete:h5glance:argument-2:*" matcher 'm:{a-z}={A-Z}'
            matching_paths=($(_h5glance_complete_infile "${line[1]}" "${line[2]}"))
            _describe "paths in file" matching_paths
            ;;
    esac
}
