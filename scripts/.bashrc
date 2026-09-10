# =============================================================================
# dellatechapps deployment shortcuts (`dt`)
# =============================================================================

# Resolve the first container id whose name contains the given substring.
# Prints the id on stdout, or nothing (and returns non-zero) if not found.
_dt_find_container() {
    local needle="$1"
    if [ -z "$needle" ]; then
        return 1
    fi
    docker ps -a --filter "name=${needle}" --format '{{.ID}}' | head -n 1
}

# Run a docker action against the first container matching a name substring.
_dt_container_action() {
    local action="$1"
    local needle="$2"
    if [ -z "$needle" ]; then
        echo "dt ${action}: missing container name" >&2
        echo "usage: dt ${action} <name>" >&2
        return 1
    fi

    local cid
    cid="$(_dt_find_container "$needle")"
    if [ -z "$cid" ]; then
        echo "dt ${action}: no container matching '${needle}'" >&2
        return 1
    fi

    local name
    name="$(docker ps -a --filter "id=${cid}" --format '{{.Names}}')"
    echo "dt ${action}: ${name} (${cid})"
    docker "$action" "$cid"
}

_dt_help() {
    cat <<'EOF'
dt - dellatechapps deployment shortcuts

Usage:
  dt ps               Show running containers (docker ps)
  dt restart <name>   Restart the first container matching <name>
  dt start <name>     Start the first container matching <name>
  dt stop <name>      Stop the first container matching <name>
  dt logs <name>      Tail logs of the first container matching <name> (last 50 lines)
  dt help             Show this help

Notes:
  <name> is a substring matched against container names; the first match wins.
  Extra arguments to `dt logs` are passed through to `docker logs`.
  Last 50 lines is the default unless you pass -n/--tail, e.g.:
    dt logs web -f            follow, last 50 lines
    dt logs web -n 200        last 200 lines
EOF
}

dt() {
    local cmd="$1"
    shift 2>/dev/null

    case "$cmd" in
        ps)
            docker ps "$@"
            ;;
        restart)
            _dt_container_action restart "$1"
            ;;
        start)
            _dt_container_action start "$1"
            ;;
        stop)
            _dt_container_action stop "$1"
            ;;
        logs)
            local needle="$1"
            shift 2>/dev/null
            if [ -z "$needle" ]; then
                echo "dt logs: missing container name" >&2
                echo "usage: dt logs <name> [docker logs options]" >&2
                return 1
            fi
            local cid
            cid="$(_dt_find_container "$needle")"
            if [ -z "$cid" ]; then
                echo "dt logs: no container matching '${needle}'" >&2
                return 1
            fi
            # Default to last 50 lines unless the caller already set -n/--tail.
            local has_tail=0
            local arg
            for arg in "$@"; do
                case "$arg" in
                    -n|--tail|--tail=*)
                        has_tail=1
                        break
                        ;;
                    --*) ;;
                    -*n*)
                        has_tail=1
                        break
                        ;;
                esac
            done
            if [ "$has_tail" -eq 0 ]; then
                docker logs -n 50 "$@" "$cid"
            else
                docker logs "$@" "$cid"
            fi
            ;;
        help|--help|-h|"")
            _dt_help
            ;;
        *)
            echo "dt: unknown command '${cmd}'" >&2
            _dt_help
            return 1
            ;;
    esac
}

# Bash tab-completion for the subcommands.
if [ -n "$BASH_VERSION" ]; then
    _dt_complete() {
        local cur="${COMP_WORDS[COMP_CWORD]}"
        if [ "$COMP_CWORD" -eq 1 ]; then
            COMPREPLY=( $(compgen -W "ps restart start stop logs help" -- "$cur") )
        elif [ "$COMP_CWORD" -eq 2 ]; then
            # Suggest container names for the second argument.
            local names
            names="$(docker ps -a --format '{{.Names}}' 2>/dev/null)"
            COMPREPLY=( $(compgen -W "${names}" -- "$cur") )
        fi
    }
    complete -F _dt_complete dt
fi

# Interactive SSH/login greeting (skip for `ssh root@host some-command`).
case $- in
    *i*) _dt_help ;;
esac
