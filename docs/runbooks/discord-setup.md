# Runbook — Configuration Discord

## 1. Créer l'application et le bot
1. https://discord.com/developers/applications → New Application.
2. Onglet **Bot** → Add Bot → copier le token (secret).
3. Activer les intents nécessaires (par défaut suffisent pour les slash
   commands).

## 2. Inviter le bot
- OAuth2 → URL Generator → scopes `bot` + `applications.commands`.
- Permissions minimales : envoyer des messages, utiliser les commandes.

## 3. Variables d'environnement
```
NOTIFICATION_GATEWAY=discord
DISCORD_BOT_TOKEN=...
DISCORD_APPLICATION_ID=...
DISCORD_GUILD_ID=...
DISCORD_CHANNEL_ID=...
DISCORD_ALLOWED_USER_IDS=123456789012345678,987654321098765432
```
> `DISCORD_ALLOWED_USER_IDS` vide = **personne** n'est autorisé (deny par défaut).

## 4. Lancer le bot
```bash
# via docker compose (service discord-bot) ou :
python -m adf.discord_bot.main
```
Sans token, le bot reste inactif (log `discord_disabled`), sans casser la stack.

## 5. Commandes
`/feature`, `/status`, `/approve`, `/request-changes`, `/pause`, `/resume`,
`/help`. Les informations sensibles sont envoyées en réponse privée (ephemeral).

## Sécurité
- Allowlist utilisateurs/serveur/canal, rate limiting, audit complet.
- Le texte utilisateur est traité comme donnée : jamais exécuté, jamais injecté
  dans un prompt système.
