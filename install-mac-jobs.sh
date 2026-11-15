#!/usr/bin/env bash
# Mac: install the hourly launchd job (at :05, so 07:05 follows GHC's ~06:50 reboot). It runs
# ghc-recover.sh, then pull-ghc-results.sh and, if that succeeded, prune-ghc-afs-results.sh. launchd cannot run scripts from ~/Documents, so they
# are copied to ~/.local/share/llm-ghc; rerun this after changing them. Pass --check-only to make
# the job only report GHC's health instead of running setup.sh there.
set -euo pipefail
# HOST (the GHC login) is passed to the job; LABEL names it.
REPO=$(cd "$(dirname "$0")" && pwd)
HOST=${HOST:-aechang@ghc40.ghc.andrew.cmu.edu}
DIR=$HOME/.local/share/llm-ghc
LABEL=${LABEL:-edu.cmu.aechang.llm-ghc}
PLIST=$HOME/Library/LaunchAgents/$LABEL.plist
mkdir -p "$DIR"
cp "$REPO/ghc-recover.sh" "$REPO/pull-ghc-results.sh" "$REPO/prune-ghc-afs-results.sh" "$DIR/"
mode=${1:-}; [ "$mode" = --check-only ] && mode=--check
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>-c</string>
    <string>"$DIR/ghc-recover.sh" $mode; "$DIR/pull-ghc-results.sh" &amp;&amp; "$DIR/prune-ghc-afs-results.sh"</string></array>
  <key>EnvironmentVariables</key><dict><key>REPO</key><string>$REPO</string><key>HOST</key><string>$HOST</string>
    <key>PATH</key><string>/usr/bin:/bin:/usr/sbin:/sbin</string></dict>
  <key>StartCalendarInterval</key><dict><key>Minute</key><integer>5</integer></dict>
  <key>StandardOutPath</key><string>$DIR/job.log</string>
  <key>StandardErrorPath</key><string>$DIR/job.log</string>
</dict></plist>
PLIST
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed $LABEL; log: $DIR/job.log; run now: launchctl kickstart gui/$(id -u)/$LABEL"
