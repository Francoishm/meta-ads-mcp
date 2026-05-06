#!/usr/bin/env bash
# remove-user.sh — révoque l'accès d'un utilisateur immédiatement.
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <username>" >&2
    exit 1
fi
USER="$1"
HTPASSWD=/etc/nginx/.htpasswd_mcp

if ! grep -q "^${USER}:" "$HTPASSWD" 2>/dev/null; then
    echo "ERREUR : utilisateur '$USER' inconnu." >&2
    exit 2
fi

htpasswd -D "$HTPASSWD" "$USER" 2>/dev/null
systemctl reload nginx
echo "✓ Utilisateur '$USER' révoqué."
