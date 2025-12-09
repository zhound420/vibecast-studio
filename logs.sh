#!/usr/bin/env bash
# VibeCast Studio - View Logs
# Follow service logs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/lib.sh"

# ============================================================================
# OPTIONS
# ============================================================================

SERVICE=""
TAIL_LINES=100
FOLLOW=true

show_help() {
    echo "Usage: ./logs.sh [service] [options]"
    echo ""
    echo "Services:"
    echo "  all         Show all logs (default)"
    echo "  backend     Backend API logs"
    echo "  worker      Celery worker logs"
    echo "  frontend    Frontend/Nginx logs"
    echo "  redis       Redis logs"
    echo "  flower      Flower task monitor logs"
    echo ""
    echo "Options:"
    echo "  -n, --tail N    Show last N lines (default: 100)"
    echo "  --no-follow     Don't follow logs, just show and exit"
    echo "  -h, --help      Show this help"
    echo ""
    echo "Examples:"
    echo "  ./logs.sh                  # Follow all logs"
    echo "  ./logs.sh backend          # Follow backend logs"
    echo "  ./logs.sh worker -n 50     # Show last 50 lines of worker logs"
    echo "  ./logs.sh --no-follow      # Show logs and exit"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--tail)
            TAIL_LINES="$2"
            shift 2
            ;;
        --no-follow)
            FOLLOW=false
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            SERVICE="$1"
            shift
            ;;
    esac
done

# ============================================================================
# MAIN LOGS FLOW
# ============================================================================

main() {
    local platform
    platform=$(load_config "platform" "cpu")

    # Determine which service to show
    local target="${SERVICE:-all}"

    case "$target" in
        all)
            show_all_logs "$platform"
            ;;
        backend)
            show_backend_logs "$platform"
            ;;
        worker)
            show_worker_logs "$platform"
            ;;
        frontend|redis|flower|beat)
            show_docker_logs "$target"
            ;;
        *)
            print_error "Unknown service: $target"
            show_help
            exit 1
            ;;
    esac
}

# ============================================================================
# LOG FUNCTIONS
# ============================================================================

show_all_logs() {
    local platform=$1

    if [[ "$platform" == "apple" ]]; then
        # For Apple Silicon, we need to combine native and Docker logs
        print_info "Showing combined logs (Ctrl+C to exit)"
        echo ""

        if [[ "$FOLLOW" == true ]]; then
            # Use a subshell to combine logs
            (
                # Docker logs
                cd "$PROJECT_ROOT"
                docker compose logs -f --tail="$TAIL_LINES" redis frontend flower 2>/dev/null &

                # Native logs
                if [[ -f "$LOG_DIR/backend.log" ]]; then
                    tail -f "$LOG_DIR/backend.log" 2>/dev/null | sed 's/^/[backend] /' &
                fi
                if [[ -f "$LOG_DIR/worker.log" ]]; then
                    tail -f "$LOG_DIR/worker.log" 2>/dev/null | sed 's/^/[worker] /' &
                fi

                # Wait for any process
                wait
            )
        else
            # Show Docker logs
            cd "$PROJECT_ROOT"
            docker compose logs --tail="$TAIL_LINES" redis frontend flower 2>/dev/null || true

            # Show native logs
            echo ""
            if [[ -f "$LOG_DIR/backend.log" ]]; then
                echo -e "${CYAN}=== Backend Logs ===${NC}"
                tail -n "$TAIL_LINES" "$LOG_DIR/backend.log" 2>/dev/null || true
            fi
            if [[ -f "$LOG_DIR/worker.log" ]]; then
                echo -e "${CYAN}=== Worker Logs ===${NC}"
                tail -n "$TAIL_LINES" "$LOG_DIR/worker.log" 2>/dev/null || true
            fi
        fi
    else
        # Docker-only mode
        show_docker_logs "all"
    fi
}

show_backend_logs() {
    local platform=$1

    if [[ "$platform" == "apple" ]]; then
        # Native backend logs
        if [[ ! -f "$LOG_DIR/backend.log" ]]; then
            print_error "Backend log file not found"
            print_info "Backend may not have been started yet"
            exit 1
        fi

        if [[ "$FOLLOW" == true ]]; then
            tail -f "$LOG_DIR/backend.log"
        else
            tail -n "$TAIL_LINES" "$LOG_DIR/backend.log"
        fi
    else
        show_docker_logs "backend"
    fi
}

show_worker_logs() {
    local platform=$1

    if [[ "$platform" == "apple" ]]; then
        # Native worker logs
        if [[ ! -f "$LOG_DIR/worker.log" ]]; then
            print_error "Worker log file not found"
            print_info "Worker may not have been started yet"
            exit 1
        fi

        if [[ "$FOLLOW" == true ]]; then
            tail -f "$LOG_DIR/worker.log"
        else
            tail -n "$TAIL_LINES" "$LOG_DIR/worker.log"
        fi
    else
        show_docker_logs "worker"
    fi
}

show_docker_logs() {
    local service=$1

    cd "$PROJECT_ROOT"

    local compose_cmd
    compose_cmd=$(docker_compose_cmd)

    local follow_flag=""
    if [[ "$FOLLOW" == true ]]; then
        follow_flag="-f"
    fi

    if [[ "$service" == "all" ]]; then
        $compose_cmd logs $follow_flag --tail="$TAIL_LINES" 2>/dev/null || {
            print_error "Failed to get logs"
            print_info "Are the services running? Check with ./status.sh"
            exit 1
        }
    else
        $compose_cmd logs $follow_flag --tail="$TAIL_LINES" "$service" 2>/dev/null || {
            print_error "Failed to get logs for $service"
            print_info "Is $service running? Check with ./status.sh"
            exit 1
        }
    fi
}

# ============================================================================
# RUN
# ============================================================================

main "$@"
