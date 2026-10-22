#!/usr/bin/env bash
#
# Deploy the Sphinx documentation site to /map.
#
# Run: sudo /usr/local/bin/deploy_sphinx
#
# Three privilege levels are used deliberately:
#   - ec2-user pulls from GitHub (it is the only user holding a deploy key)
#   - teledocs builds the docs   (Sphinx executes arbitrary Python from the
#                                 repo, so it must never run as root)
#   - root publishes the output  (the web root stays root-owned and read-only
#                                 to the service user)

set -euo pipefail

SRC_REPO="/home/ec2-user/documents_map"
BUILD_DIR="/home/teledocs/documents_map"
WEB_ROOT="/usr/share/nginx/html/documents_index/map"
SPHINX="/home/teledocs/packages/anaconda3/envs/dis/bin/sphinx-build"
BUILD_USER="teledocs"

die() { echo "deploy_sphinx: $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "must be run with sudo"
[[ -d "$SRC_REPO/.git" ]] || die "no clone at $SRC_REPO -- clone it as ec2-user first"
[[ -x "$SPHINX" ]] || die "sphinx-build not found at $SPHINX"

# Step 4 publishes with rsync --delete, so a WEB_ROOT pointing one level up
# would wipe the main site. Nothing else here reaches outside /map.
[[ "$WEB_ROOT" == */map ]] || die "WEB_ROOT must end in /map -- refusing to rsync --delete"

# sudo -u inherits the cwd, and homes are mode 700, so a deployer's home would
# be unreadable to teledocs. Every path below is absolute.
cd /

# 1. Pull as ec2-user so the GitHub key is the one in ec2-user's ~/.ssh.
#    The before/after report is the only view a deployer gets of what is being
#    published -- the clone itself is not readable to them.
echo "==> Pulling $SRC_REPO"
before=$(sudo -u ec2-user -H git -C "$SRC_REPO" rev-parse HEAD)
sudo -u ec2-user -H git -C "$SRC_REPO" pull --ff-only
after=$(sudo -u ec2-user -H git -C "$SRC_REPO" rev-parse HEAD)

if [[ "$before" == "$after" ]]; then
  echo "    no new commits; still at ${after:0:8} -- rebuilding anyway"
else
  echo "    ${before:0:8} -> ${after:0:8}"
  sudo -u ec2-user -H git -C "$SRC_REPO" log --oneline "$before..$after"
fi

# 2. Hand the sources to teledocs. The clone itself is never exposed; only a
#    copy of the working tree, without .git, ends up under teledocs.
echo "==> Syncing sources to $BUILD_DIR"
install -d -o "$BUILD_USER" -g "$BUILD_USER" -m 755 "$BUILD_DIR"
rsync -a --delete --exclude '.git' --exclude '_build' --exclude '.doctrees' \
  --chown="$BUILD_USER:$BUILD_USER" \
  "$SRC_REPO/" "$BUILD_DIR/"

# 3. Build unprivileged.
#    -E  re-read every source file; never trust the cached environment
#    -a  write all output, so a change under _static/ alone still republishes
#    -d  keep the doctree cache out of $BUILD_DIR/_build, which is published
echo "==> Building docs as $BUILD_USER"
sudo -u "$BUILD_USER" -H "$SPHINX" -b html -E -a \
  -d "$BUILD_DIR/.doctrees" \
  "$BUILD_DIR" "$BUILD_DIR/_build"

[[ -f "$BUILD_DIR/_build/index.html" ]] || die "build produced no index.html"

# 4. Publish. --delete removes pages that were deleted upstream; a plain
#    'cp -r' would leave them behind forever.
echo "==> Publishing to $WEB_ROOT"
install -d -o root -g root -m 755 "$WEB_ROOT"
rsync -a --delete \
  --chown=root:root --chmod=D755,F644 \
  "$BUILD_DIR/_build/" "$WEB_ROOT/"

# nginx serves static files straight from disk, so the pages are live as soon
# as the rsync above finishes -- no reload or restart is needed to publish.
echo "==> Done. ${after:0:8} is now live at https://teledocs.space/map/"
