#!/usr/bin/env bash
# VibeCast Studio - Stop Application
# Gracefully stops all services

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/lib.sh"

# ============================================================================
# OPTIONS
# ============================================================================

QUIET=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -q|--quiet)
            QUIET=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            echo "Usage: ./stop.sh [options]"
            echo ""
            echo "Options:"
            echo "  -q, --quiet    Suppress output"
            echo "  --clean        Also remove Docker volumes"
            echo "  -h, --help     Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ============================================================================
# MAIN STOP FLOW
# ============================================================================

main() {
    if [[ "$QUIET" == false ]]; then
        print_header "Stop           "
        print_info "Stopping VibeCast Studio..."
        echo ""
    fi

    local platform
    platform=$(load_config "platform" "cpu")

    # Stop native processes first (Apple Silicon)
    if [[ "$platform" == "apple" ]]; then
        stop_native_processes
    fi

    # Stop Docker containers
    stop_docker_services

    # Clean if requested
    if [[ "$CLEAN" == true ]]; then
        clean_docker_volumes
    fi

    if [[ "$QUIET" == false ]]; then
        echo ""
        print_success "VibeCast Studio stopped"
        echo ""
    fi
}

# ============================================================================
# STOP FUNCTIONS
# ============================================================================

stop_native_processes() {
    if [[ "$QUIET" == false ]]; then
        print_step "Stopping native processes..."
    fi

    # Stop backend
    if is_process_running "backend"; then
        kill_process "backend"
        if [[ "$QUIET" == false ]]; then
            print_success "Backend stopped"
        fi
    fi

    # Stop worker
    if is_process_running "worker"; then
        kill_process "worker"
        if [[ "$QUIET" == false ]]; then
            print_success "Worker stopped"
        fi
    fi

    # Clean up any orphaned processes on ports
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true

    if [[ "$QUIET" == false ]]; then
        echo ""
    fi
}

stop_docker_services() {
    if [[ "$QUIET" == false ]]; then
        print_step "Stopping Docker services..."
    fi

    cd "$PROJECT_ROOT"

    local platform
    platform=$(load_config "platform" "cpu")

    if [[ "$platform" == "nvidia" ]]; then
        docker compose -f docker-compose.yml -f docker-compose.nvidia.yml down &>/dev/null || true
    else
        docker compose down &>/dev/null || true
    fi

    if [[ "$QUIET" == false ]]; then
        print_success "Docker services stopped"
    fi
}

clean_docker_volumes() {
    if [[ "$QUIET" == false ]]; then
        print_step "Removing Docker volumes..."
    fi

    cd "$PROJECT_ROOT"

    local platform
    platform=$(load_config "platform" "cpu")

    if [[ "$platform" == "nvidia" ]]; then
        docker compose -f docker-compose.yml -f docker-compose.nvidia.yml down -v &>/dev/null || true
    else
        docker compose down -v &>/dev/null || true
    fi

    if [[ "$QUIET" == false ]]; then
        print_success "Docker volumes removed"
    fi
}

# ============================================================================
# RUN
# ============================================================================

main "$@"
