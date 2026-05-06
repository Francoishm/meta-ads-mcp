# Connecter Claude Desktop au serveur Meta Ads SOFIT

> Guide pour utilisateur final — aucune compétence technique requise.
> Temps : ~5 minutes.

## Pré-requis

1. **Claude Desktop** installé sur ton Mac/PC
   → Téléchargement : https://claude.ai/download
2. Un **identifiant + mot de passe** fournis par l'admin (François)

Si tu n'as pas reçu tes identifiants, demande-les sur Slack/email.

## Étape 1 — Localiser ton fichier de config

Selon ton système :

| OS | Chemin |
|----|--------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |

Pour l'ouvrir facilement :

**macOS** : ouvre le Finder, tape `Cmd+Shift+G`, colle le chemin → Enter

**Windows** : tape `%APPDATA%\Claude\` dans l'explorateur

## Étape 2 — Éditer le fichier

Ouvre `claude_desktop_config.json` avec TextEdit / Notepad.

### Cas A : le fichier est vide ou n'existe pas

Crée-le avec ce contenu (en remplaçant `MON_USER` et `MON_PASS` par tes identifiants) :

```json
{
  "mcpServers": {
    "meta-ads": {
      "url": "https://MON_USER:MON_PASS@dev.sofit.studio/meta-ads-mcp/sse"
    }
  }
}
```

### Cas B : le fichier existe déjà

Cherche la clé `mcpServers`.

**Si elle existe**, ajoute juste l'entrée `"meta-ads"` à l'intérieur :

```json
{
  "mcpServers": {
    "...autre serveur existant...": { ... },
    "meta-ads": {
      "url": "https://MON_USER:MON_PASS@dev.sofit.studio/meta-ads-mcp/sse"
    }
  }
}
```

**Si elle n'existe pas**, ajoute le bloc complet `mcpServers` au même niveau que les autres clés :

```json
{
  "preferences": { ... },
  "mcpServers": {
    "meta-ads": {
      "url": "https://MON_USER:MON_PASS@dev.sofit.studio/meta-ads-mcp/sse"
    }
  }
}
```

⚠ Attention aux **virgules** : chaque entrée doit en avoir une, sauf la dernière.

## Étape 3 — Redémarrer Claude Desktop

1. Quitte complètement Claude Desktop (`Cmd+Q` sur Mac, fermer + clic droit dans la barre des tâches Windows)
2. Relance-le

## Étape 4 — Vérifier que ça marche

Dans une nouvelle conversation Claude :

1. Clique sur l'icône **🔌** ou **« Outils »** en bas de la zone de saisie
2. Tu dois voir un serveur **`meta-ads`** avec **29 outils** dispo
3. Pose une question type :

> *« Liste les comptes publicitaires Meta auxquels j'ai accès »*

Claude devrait appeler l'outil `list_ad_accounts` et te retourner la liste.

## Que peut faire Claude avec ce serveur ?

Mode actuel : **lecture + écriture** (création de campagnes possible).

Exemples de demandes :

- *« Donne-moi le spend, CTR et CPC de la campagne X sur les 30 derniers jours »*
- *« Quelles sont les 5 campagnes avec le pire ROAS ce mois-ci ? »*
- *« Crée une nouvelle campagne PAUSED, objectif Leads, budget 30€/jour, ciblage femmes 30-50 Île-de-France intéressées par fitness »*
- *« Pause toutes les campagnes qui ont dépensé plus de 100€ pour moins de 5 conversions »*

⚠ **Sécurité** : par défaut toute campagne créée est en **statut PAUSED** (ne dépense pas). Il faut explicitement la passer en ACTIVE depuis Meta Ads Manager pour qu'elle démarre.

## Problèmes fréquents

### « Je ne vois pas le serveur dans Claude Desktop »

- Vérifie qu'il n'y a pas d'erreur de syntaxe JSON (utilise https://jsonlint.com)
- Vérifie que tu as bien quitté **complètement** Claude (pas juste fermé la fenêtre)
- Vérifie que l'URL est exactement `https://USER:PASS@dev.sofit.studio/meta-ads-mcp/sse`

### « Le serveur est listé mais les appels échouent »

Teste tes identifiants depuis le terminal :

```bash
curl -s -u 'TON_USER:TON_PASS' --max-time 3 https://dev.sofit.studio/meta-ads-mcp/sse | head -c 100
```

Tu dois voir :
```
event: endpoint
data: /meta-ads-mcp/messages/?session_id=...
```

Si tu vois `401 Unauthorized` → tes identifiants sont mauvais, contacte l'admin.

Si tu vois `502 Bad Gateway` ou pas de réponse → le serveur est en panne, contacte l'admin.

### « Je veux changer mon mot de passe »

Demande-le à l'admin, qui exécute `./rotate-user.sh ton.username` côté serveur.

### « Je veux désinstaller »

Retire l'entrée `"meta-ads"` du fichier `claude_desktop_config.json` et redémarre Claude Desktop.
