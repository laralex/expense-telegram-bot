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
DEFAULT_RESTORE_TARGET="$BACKUP_DATA_DIR"

# Colors
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[1;33m'

# --- Helper Functions ---
show_help() {
    cat <<EOF
Usage: $(basename "$0") <command> [archive_path]

Commands:
  backup <archive_path>  Create an archive from the source directory
  restore <archive_path> Restore the source directory from the archive

Commands use source directory from config.sh:
  backup: Source=$DEFAULT_SOURCE_DIR
  restore: Target=$DEFAULT_RESTORE_TARGET

EOF
}

error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# --- Command Implementations ---
do_backup() {
    local source_dir="$DEFAULT_SOURCE_DIR"
    local output_archive="$1"

    if [[ -z "$output_archive" ]]; then
        error_exit "You must specify an archive path for the backup (e.g., ./backup.sh backup my_backup.tar.gz)"
    fi

    echo "[INFO] Starting backup of '$source_dir' into '$output_archive'..."

    if [[ ! -d "$source_dir" ]]; then
        error_exit "Source directory '$source_dir' does not exist."
    fi

    # Conflict check: Archive already exists
    if [[ -f "$output_archive" ]]; then
        error_exit "Archive '$output_archive' already exists."
    fi

    # Ensure the output directory exists
    mkdir -p "$(dirname "$output_archive")"

    if tar -czf "$output_archive" "$source_dir"; then
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

    # Conflict check: Target directory is not empty
    if [[ -d "$target_dir" ]] && [[ -n "$(ls -A "$target_dir" 2>/dev/null)" ]]; then
        error_exit "Target directory '$target_dir' is not empty."
    fi

    # Create target directory if it doesn't exist
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