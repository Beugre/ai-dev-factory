#!/usr/bin/env bash
# Setup initial du VPS — à exécuter UNE SEULE FOIS en root.
# Usage : ssh BOT-VPS 'bash -s' < infra/scripts/setup-vps.sh
set -euo pipefail

echo "=== Installation Docker ==="
apt-get update -qq
apt-get install -y --no-install-recommends \
  ca-certificates curl gnupg lsb-release git ufw

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -qq
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

systemctl enable --now docker

echo "=== Firewall ==="
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "=== Répertoire app ==="
mkdir -p /opt/ai-dev-factory
cd /opt/ai-dev-factory

echo "=== Cloner le repo ==="
if [ ! -d ".git" ]; then
  git clone https://github.com/Beugre/ai-dev-factory.git .
else
  git pull origin main
fi

echo "✅ Setup VPS terminé."
echo "Prochaine étape : copier le fichier .env sur le VPS et lancer deploy.sh"
