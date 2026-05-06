#!/usr/bin/env bash
# rotate-user.sh — change le mot de passe d'un utilisateur existant.
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <username>" >&2
    exit 1
fi
USER="$1"
HTPASSWD=/etc/nginx/.htpasswd_mcp

if ! grep -q "^${USER}:" "$HTPASSWD" 2>/dev/null; then
    echo "ERREUR : utilisateur '$USER' n'existe pas." >&2
    echo "Pour le créer : ./add-user.sh $USER" >&2
    exit 2
fi

PWD_PLAIN=$(openssl rand -base64 24 | tr -d '/+=' | head -c 28)
htpasswd -bB "$HTPASSWD" "$USER" "$PWD_PLAIN" 2>/dev/null
systemctl reload nginx

echo "Mot de passe rotaté pour '$USER' :"
echo "  Username : $USER"
echo "  Password : $PWD_PLAIN"
echo ""
echo "URL Claude Desktop : https://${USER}:${PWD_PLAIN}@dev.sofit.studio/meta-ads-mcp/sse"
