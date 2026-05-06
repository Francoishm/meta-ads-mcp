#!/usr/bin/env bash
# add-user.sh — onboarding multi-utilisateur sur le serveur SSE.
#
# Crée un nouvel utilisateur Basic Auth dans /etc/nginx/.htpasswd_mcp,
# génère un mot de passe aléatoire, et imprime le snippet de config
# prêt à coller dans Claude Desktop côté utilisateur final.
#
# Usage (sur le serveur, en root) :
#   ./add-user.sh prenom.nom
#   ./add-user.sh equipe-marketing

set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <username>" >&2
    exit 1
fi

USER="$1"
HTPASSWD=/etc/nginx/.htpasswd_mcp
PUBLIC_URL="${PUBLIC_URL:-https://dev.sofit.studio/meta-ads-mcp/sse}"

# Validation user (alphanum + . - _)
if ! [[ "$USER" =~ ^[a-zA-Z0-9._-]+$ ]]; then
    echo "Username invalide (a-z 0-9 . _ - uniquement)" >&2
    exit 1
fi

# Vérifier qu'on a htpasswd installé
if ! command -v htpasswd >/dev/null 2>&1; then
    apt-get install -y apache2-utils >/dev/null
fi

# Refuser overwrite silencieux
if grep -q "^${USER}:" "$HTPASSWD" 2>/dev/null; then
    echo "ERREUR : utilisateur '$USER' existe déjà." >&2
    echo "Pour rotater son mot de passe : ./rotate-user.sh $USER" >&2
    exit 2
fi

# Mot de passe aléatoire
PWD_PLAIN=$(openssl rand -base64 24 | tr -d '/+=' | head -c 28)

# Ajouter à htpasswd (le -B = bcrypt)
htpasswd -bB "$HTPASSWD" "$USER" "$PWD_PLAIN" 2>/dev/null
chmod 640 "$HTPASSWD"
chown root:www-data "$HTPASSWD" 2>/dev/null || true

# Reload nginx (transparent, pas de coupure)
systemctl reload nginx

# Affichage (à transmettre à l'utilisateur via canal sécurisé)
cat <<EOF

┌─────────────────────────────────────────────────────────────┐
│  ✓ Utilisateur '$USER' créé sur le serveur Meta Ads MCP   │
└─────────────────────────────────────────────────────────────┘

URL       : $PUBLIC_URL
Username  : $USER
Password  : $PWD_PLAIN

─── Snippet à coller dans Claude Desktop ────────────────────

Fichier : ~/Library/Application Support/Claude/claude_desktop_config.json
(macOS)   ou %APPDATA%\\Claude\\claude_desktop_config.json (Windows)

{
  "mcpServers": {
    "meta-ads": {
      "url": "https://${USER}:${PWD_PLAIN}@dev.sofit.studio/meta-ads-mcp/sse"
    }
  }
}

⚠  Si la clé "mcpServers" existe déjà, ajouter SEULEMENT
   l'entrée "meta-ads": {...} à l'intérieur (ne pas écraser
   les autres serveurs MCP).

Puis Quit + relancer Claude Desktop.

─── Vérification ──────────────────────────────────────────────

curl -s -u '${USER}:${PWD_PLAIN}' \\
     --max-time 3 $PUBLIC_URL | head -c 100
# Doit afficher : event: endpoint / data: /meta-ads-mcp/messages/...

EOF
