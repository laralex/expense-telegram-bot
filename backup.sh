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
GREEN='\033[0;32m'

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

    # Get base name of archive (e.g., backup.tar.gz -> backup)
    local archive_basename
    archive_basename=$(basename "$output_archive" | sed 's/\.tar\.gz$//')

    # Create a temporary staging area
    staging_dir=$(mktemp -d)

    # Ensure staging directory is cleaned up on exit
    trap 'rm -rf "$staging_dir"' EXIT

    # Create the subfolder in staging area
    local archive_content_dir="$staging_dir/$archive_basename"
    mkdir -p "$archive_content_dir"

    # Copy files to staging area
    if [[ -f "$service_root/.env" ]]; then
        cp "$service_root/.env" "$archive_content_dir/"
    else
        echo -e "${YELLOW}[WARN] .env not found in $service_root. Only $data_dirname/ will be included.${NC}"
    fi

    if [[ -d "$source_dir" ]]; then
        cp -r "$source_dir" "$archive_content_dir/"
    else
        error_exit "Source directory '$source_dir' does not exist."
    fi

    # Create the archive from the staging directory
    if tar -czf "$output_archive" -C "$staging_dir" "$archive_basename"; then
        echo "Successfully created backup: $output_archive (contains /$archive_basename/)"
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

    # Get the name of the top-level directory inside the archive
    # We take the first line, and strip any trailing slashes
    local top_dir
    top_dir=$(tar -tf "$archive_file" | head -n 1 | sed 's|/||')
    
    if [[ -z "$top_dir" ]]; then
        error_exit "Archive seems to be empty or invalid."
    fi

    echo "[INFO] Checking for conflicts in '$target_dir'..."

    local conflicts=()
    # Iterate through all entries in the archive
    while read -r line; do
        [[ -z "$line" ]] && continue
        
        # Skip if the entry is just the top-level directory itself
        # Handle both "top_dir/" and "top_dir"
        if [[ "$line" == "$top_dir/" ]] || [[ "$line" == "$top_dir" ]]; then
            continue
        fi

        # Strip the top-level directory prefix to get the relative path
        # This handles "top_dir/path/to/file" -> "path/to/file"
        local relative_path
        relative_path=$(echo "$line" | sed "s|^$top_dir/||")
        
        local check_path="$target_dir/$relative_path"
        if [[ -e "$check_path" ]]; then
            conflicts+=("$relative_path")
        fi
    done < <(tar -tf "$archive_file")

    if [[ ${#conflicts[@]} -gt 0 ]]; then
        echo -e "${RED}ERROR: Restoration aborted due to the following conflicts:${NC}"
        # Remove duplicate conflicts and sort them
        printf '%s\n' "${conflicts[@]}" | sort | uniq | while read -r conflict; do
            echo "  - $conflict"
        done
        error_exit "Conflicts detected. Use a different target directory or clear the current one."
    fi

    # Create target directory if it doesn't exist
    mkdir -p "$target_dir"

    # Extracting using --strip-components=1 to remove the top-level folder inside the archive
    if tar -xzf "$archive_file" -C "$target_dir" --strip-components=1; then
        echo -e "${GREEN}Successfully restored archive to '$target_dir'.${NC}"
    else
        error_exit "Failed to restore archive. Ensure it contains a single root folder."
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