#!/usr/bin/env bash
# Installs the probe-feature skill library into ~/.claude/skills/.
# Walks skills/ for SKILL.md files and copies each containing folder to
# ~/.claude/skills/<leaf-name>/.

set -euo pipefail

DRY_RUN=0
# MODE is empty until the user/flags choose: overwrite | skip | archive | ""
MODE=""
set_mode() {
    if [[ -n "$MODE" && "$MODE" != "$1" ]]; then
        echo "conflicting collision flags: --$MODE and --$1" >&2; exit 2
    fi
    MODE="$1"
}
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --force|--overwrite) set_mode overwrite ;;
        --skip) set_mode skip ;;
        --archive) set_mode archive ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
    shift
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="$REPO_ROOT/skills"
DEST_ROOT="$HOME/.claude/skills"
ARCHIVE_ROOT="$DEST_ROOT/.archive"

[[ -d "$SKILLS_ROOT" ]] || { echo "skills/ folder not found at $SKILLS_ROOT" >&2; exit 1; }

run() {
    if [[ $DRY_RUN -eq 1 ]]; then echo "[dry-run] $*"; else eval "$*"; fi
}

# Decide the collision mode the first time it is needed (interactive only).
ASKED_GLOBAL=0
ensure_mode() {
    [[ -n "$MODE" ]] && return
    [[ $ASKED_GLOBAL -eq 1 ]] && return
    ASKED_GLOBAL=1
    echo "Existing skills collide. Apply which action to ALL collisions?"
    read -r -p "  (o)verwrite-all / (s)kip-all / (a)rchive-all / (d)ecide-each: " g
    case "$g" in
        o|O) MODE=overwrite ;;
        s|S) MODE=skip ;;
        a|A) MODE=archive ;;
        *)   MODE="" ;;   # decide-each: fall through to per-skill prompt
    esac
}

run "mkdir -p '$DEST_ROOT'"

# Collect leaf skill folders, excluding shared/templates.
mapfile -t LEAVES < <(find "$SKILLS_ROOT" -name 'SKILL.md' -type f | while read -r f; do
    d="$(dirname "$f")"
    [[ "$d" == *"shared/templates"* ]] && continue
    echo "$d"
done)

echo "Found ${#LEAVES[@]} skill folders to install."

# Offer to archive prototypes on first run.
PROTOTYPES=(probe scope grill-me)
EXISTING=()
for p in "${PROTOTYPES[@]}"; do
    [[ -d "$DEST_ROOT/$p" ]] && EXISTING+=("$p")
done
if [[ ${#EXISTING[@]} -gt 0 ]]; then
    echo "Found existing prototype skills: ${EXISTING[*]}"
    if [[ -n "$MODE" ]]; then ans=y; else read -r -p "Archive these before installing the new library? (y/N) " ans; fi
    if [[ "$ans" == "y" || "$ans" == "Y" ]]; then
        run "mkdir -p '$ARCHIVE_ROOT'"
        for p in "${EXISTING[@]}"; do
            stamp="$(date +%Y%m%d-%H%M%S)"
            run "mv '$DEST_ROOT/$p' '$ARCHIVE_ROOT/$p-$stamp'"
            echo "Archived $p -> .archive/$p-$stamp"
        done
    fi
fi

installed=0; skipped=0; overwritten=0
for leaf in "${LEAVES[@]}"; do
    name="$(basename "$leaf")"
    dst="$DEST_ROOT/$name"

    if [[ -d "$dst" ]]; then
        ensure_mode
        if [[ "$MODE" == overwrite ]]; then action=o
        elif [[ "$MODE" == skip ]]; then action=s
        elif [[ "$MODE" == archive ]]; then action=a
        else
            read -r -p "Skill '$name' already exists. (o)verwrite / (s)kip / (a)rchive-then-overwrite? " action
        fi
        case "$action" in
            o)
                run "rm -rf '$dst'"
                run "cp -r '$leaf' '$dst'"
                overwritten=$((overwritten+1))
                ;;
            a)
                stamp="$(date +%Y%m%d-%H%M%S)"
                run "mkdir -p '$ARCHIVE_ROOT'"
                run "mv '$dst' '$ARCHIVE_ROOT/$name-$stamp'"
                run "cp -r '$leaf' '$dst'"
                overwritten=$((overwritten+1))
                ;;
            *)
                echo "Skipped $name"; skipped=$((skipped+1))
                ;;
        esac
    else
        run "cp -r '$leaf' '$dst'"
        installed=$((installed+1))
    fi
done

echo
echo "Summary: $installed installed, $overwritten overwritten/archived, $skipped skipped."
