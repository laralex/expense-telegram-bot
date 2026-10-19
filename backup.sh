#!/bin/bash
set -euo pipefail

if [[ ! -f config.sh ]]; then
    echo "ERROR: config.sh not found. Please create it first." >&2
    exit 1
fi

source config.sh

# --- Configuration & Defaults ---
# Source and target paths are taken from config.sh
DEFAULT_SOURCE_DIR="$BACKUP_DATA_DIR"
# Default restore target is now the service root to include .env and data/
DEFAULT_RESTORE_TARGET="$(dirname "$BACKUP_DATA_DIR")"

# Colors
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[1;33m'

# --- Helper Functions ---
show_help() {
    cat <<EOF
Usage: $(basename "$0") <command> [archive_path]

Commands:
  backup <archive_path>  Create an archive from the service root (includes .env and data/)
  restore <archive_path> Restore the service root from the archive

Commands use:
  backup source: $DEFAULT_SOURCE_DIR (plus .env)
  restore target: $DEFAULT_RESTORE_TARGET

EOF
}

error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# --- Command Implementations ---
do_backup() {
    local source_dir="$DEFAULT_SOURCE_DIR"
    local service_root="$(dirname "$source_dir")"
    local data_dirname=$(basename "$source_dir")
    local output_archive="$1"

    if [[ -z "$output_archive" ]]; then
        error_exit "You must specify an archive path for the backup (e.g., ./backup.sh backup my_backup.tar.gz)"
    fi

    echo "[INFO] Starting backup of service root (including $data_dirname/ and .env) into '$output_archive'..."

    if [[ ! -d "$service_root" ]]; then
        error_exit "Service root '$service_root' does not exist."
    fi

    # Conflict check: Archive already exists
    if [[ -f "$output_archive" ]]; then
        error_exit "Archive '$output_archive' already exists."
    fi

    # Ensure the output directory exists
    mkdir -p "$(dirname "$output_archive")"

    # Prepare files to include
    local files_to_include=("$data_dirname")
    if [[ -f "$service_root/.env" ]]; then
        files_to_include=(".env" "${files_to_include[@]}")
    else
        echo -e "${YELLOW}[WARN] .env not found in $service_root. Only $data_dirname/ will be included.${NC}"
    fi

    if tar -czf "$output_archive" -C "$service_root" "${files_to_include[@]}"; then
        echo "Successfully created backup: $output_archive"
    else
        error_exit "Failed to create archive."
    fi
}

do_restore() {
    local archive_file="$1"
    local target_dir="$DEFAULT_RESTORE_TARGET"

    if [[ -z "$archive_file" ]]; then
        error_exit "You must specify an archive path for the restore (e.g., ./backup.sh restore my_backup.tar.gz)"
    fi

    echo "[INFO] Starting restoration of '$archive_file' to '$target_dir'..."

    if [[ ! -f "$archive_file" ]]; then
        error_exit "Archive file '$archive_file' does not exist."
    fi

    # We allow overwriting files in the target directory during restore
    mkdir -p "$target_dir"

    # Extracting
    if tar -xzf "$archive_file" -C "$target_dir"; then
        echo "Successfully restored archive to '$target_dir'."
    else
        error_exit "Failed to restore archive."
    fi
}

# --- Main Entry Point ---

COMMAND=""

# Manual flag parsing
while [[ $# -gt 0 ]]; do
    case "$1" in
        backup|restore)
            COMMAND="$1"
            shift
            break
            ;;
        *)
            error_exit "Unknown command or option: $1. Use --help for usage."
            ;;
    esac
done

case "$COMMAND" in
    backup)
        do_backup "$@"
        ;;
    restore)
        do_restore "$@"
        ;;
    *)
        if [[ -z "$COMMAND" ]]; then
            show_help
        else
            error_exit "Unknown command: $COMMAND"
        fi
        ;;
esac