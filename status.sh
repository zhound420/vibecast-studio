#!/usr/bin/env bash
# VibeCast Studio - Check Status
# Shows current state of all services

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/lib.sh"

# ============================================================================
# MAIN STATUS FLOW
# ============================================================================

main() {
    print_header "Status         "

    local platform
    platform=$(load_config "platform" "cpu")

    echo -e "  Platform: ${CYAN}$(get_platform_name "$platform")${NC}"
    echo ""

    # Show service status
    echo -e "${BOLD}Services:${NC}"
    echo ""

    show_docker_status

    if [[ "$platform" == "apple" ]]; then
        show_native_status
    fi

    echo ""

    # Show health checks
    echo -e "${BOLD}Health Checks:${NC}"
    echo ""
    show_health_checks

    echo ""

    # Show URLs if running
    if check_backend_health || check_frontend_health; then
        echo -e "${BOLD}Access URLs:${NC}"
        echo ""
        print_url "Frontend" "http://localhost:3000"
        print_url "API Docs" "http://localhost:8000/docs"
        print_url "Flower  " "http://localhost:5555"
        echo ""
    fi
}

# ============================================================================
# STATUS FUNCTIONS
# ============================================================================

show_docker_status() {
    cd "$PROJECT_ROOT"

    local platform
    platform=$(load_config "platform" "cpu")

    local services
    if [[ "$platform" == "apple" ]]; then
        services=("redis" "frontend" "flower")
    else
        services=("redis" "backend" "worker" "beat" "frontend" "flower")
    fi

    for service in "${services[@]}"; do
        local status
        status=$(get_container_status "$service" 2>/dev/null || echo "not running")

        if [[ "$status" == *"Up"* ]] || [[ "$status" == *"running"* ]]; then
            echo -e "  ${GREEN}●${NC} $service ${DIM}($status)${NC}"
        elif [[ "$status" == "not running" ]] || [[ -z "$status" ]]; then
            echo -e "  ${RED}○${NC} $service ${DIM}(stopped)${NC}"
        else
            echo -e "  ${YELLOW}●${NC} $service ${DIM}($status)${NC}"
        fi
    done
}

show_native_status() {
    echo ""
    echo -e "  ${DIM}Native Processes:${NC}"

    # Backend
    if is_process_running "backend"; then
        local pid
        pid=$(get_pid "backend")
        echo -e "  ${GREEN}●${NC} backend ${DIM}(PID: $pid)${NC}"
    else
        echo -e "  ${RED}○${NC} backend ${DIM}(stopped)${NC}"
    fi

    # Worker
    if is_process_running "worker"; then
        local pid
        pid=$(get_pid "worker")
        echo -e "  ${GREEN}●${NC} worker ${DIM}(PID: $pid)${NC}"
    else
        echo -e "  ${RED}○${NC} worker ${DIM}(stopped)${NC}"
    fi
}

show_health_checks() {
    # Backend health
    if check_backend_health; then
        echo -e "  ${GREEN}✓${NC} Backend API is healthy"
    else
        echo -e "  ${RED}✗${NC} Backend API is not responding"
    fi

    # Frontend health
    if check_frontend_health; then
        echo -e "  ${GREEN}✓${NC} Frontend is healthy"
    else
        echo -e "  ${RED}✗${NC} Frontend is not responding"
    fi

    # Redis health
    if check_redis_health; then
        echo -e "  ${GREEN}✓${NC} Redis is healthy"
    else
        echo -e "  ${RED}✗${NC} Redis is not responding"
    fi
}

# ============================================================================
# RUN
# ============================================================================

main "$@"
