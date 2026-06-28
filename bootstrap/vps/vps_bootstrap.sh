#!/bin/bash
# VPS Bootstrap -- shared setup script for Debian 12 (bookworm) instances.
# Provisions a fresh VPS: Docker, SSH hardening, firewall, fail2ban,
# unattended-upgrades.
# Idempotent -- delete /etc/.vps-setup-done to force re-run.
#
# Works on any provider (Aliyun, Vultr, Hetzner, etc.).
# Usage -- provider startup script:
#   Paste into the "Startup Script" / "User Data" field when creating
#   a Debian 12 instance.
#
# Usage -- manual run (e.g., provider without startup-script support):
#   ssh root@<ip> 'bash -s' < vps_bootstrap.sh
#
set -euo pipefail

SENTINEL="/etc/.vps-setup-done"

if [[ -f "$SENTINEL" ]]; then
    echo "= Setup already completed ($(cat "$SENTINEL"))."
    echo "= Remove $SENTINEL to force re-run."
    exit 0
fi

echo "==> Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq

# ===========================================================================
# Docker Engine + Compose plugin
# ===========================================================================
echo "==> Installing Docker Engine..."
if ! command -v docker &>/dev/null; then
    if ! curl -fsSL --connect-timeout 5 --max-time 10 \
        "https://download.docker.com/linux/debian/gpg" -o /dev/null 2>/dev/null; then
        echo "!! Cannot reach download.docker.com — skipping Docker."
    else
        apt-get install -y -qq ca-certificates curl
        install -m 0755 -d /etc/apt/keyrings
        DOCKER_BASE="https://download.docker.com/linux/debian"

        curl -fsSL "${DOCKER_BASE}/gpg" -o /etc/apt/keyrings/docker.asc
        chmod a+r /etc/apt/keyrings/docker.asc
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] ${DOCKER_BASE} $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
            > /etc/apt/sources.list.d/docker.list
        apt-get update -qq
        apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
        systemctl enable docker
    fi
fi

# ===========================================================================
# SSH hardening --- port 9906, key-only, no password auth
# ===========================================================================
echo "==> Hardening SSH..."

# OpenSSH reads drop-in files in sorted order; first value wins for
# most directives.  Debian cloud images ship 50-cloud-init.conf which
# can set Port 22 and PasswordAuthentication yes.  We write a 00- prefixed
# drop-in so our settings take priority over everything else in that
# directory.
cat > /etc/ssh/sshd_config.d/00-hardening.conf <<'SSHEOF'
Port 9906
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
SSHEOF

# Remove any conflicting Port / PasswordAuthentication from the main
# config (usually commented out on Debian, but be safe).
sed -i '/^Port /d'                       /etc/ssh/sshd_config
sed -i '/^PasswordAuthentication /d'     /etc/ssh/sshd_config

# Re-validate auth state just in case a later drop-in overrode us
chmod 600 /etc/ssh/sshd_config.d/00-hardening.conf

if sshd -t; then
    systemctl restart sshd
    echo "   SSH now on port 9906 (key auth only)."
else
    echo "!! sshd config syntax error --- removing drop-in"
    rm -f /etc/ssh/sshd_config.d/00-hardening.conf
    systemctl restart sshd
    exit 1
fi

# ===========================================================================
# Tailscale --- mesh VPN for SSH and internal services
# ===========================================================================
echo "==> Installing Tailscale..."
if ! command -v tailscale &>/dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
    systemctl enable tailscaled
fi

# ===========================================================================
# Runtime dependencies for per-host scripts
# ===========================================================================
echo "==> Installing runtime dependencies..."
apt-get install -y -qq git nodejs python3-yaml rsync

# ===========================================================================
# UFW firewall --- allow SSH (9906), HTTP, HTTPS
# ===========================================================================
echo "==> Configuring UFW firewall..."
apt-get install -y -qq ufw

ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 9906/tcp comment 'SSH'
ufw allow 80/tcp   comment 'HTTP'
ufw allow 443/tcp  comment 'HTTPS'
ufw allow 443/udp  comment 'HTTP/3 QUIC'
ufw allow in on tailscale0 comment 'Tailscale mesh'
ufw --force enable

# ===========================================================================
# fail2ban --- brute-force protection for SSH
# ===========================================================================
echo "==> Installing fail2ban..."
apt-get install -y -qq fail2ban rsyslog

cat > /etc/fail2ban/jail.local <<'F2BEOF'
[DEFAULT]
bantime   = 1h
findtime  = 10m
maxretry  = 5

[sshd]
enabled   = true
port      = 9906
logpath   = /var/log/auth.log
F2BEOF

systemctl restart fail2ban

# ===========================================================================
# unattended-upgrades --- automatic security patches
# ===========================================================================
echo "==> Enabling unattended-upgrades..."
apt-get install -y -qq unattended-upgrades apt-listchanges

cat > /etc/apt/apt.conf.d/50unattended-upgrades <<'UEOF'
Unattended-Upgrade::Origins-Pattern {
    "origin=Debian,codename=${distro_codename},label=Debian-Security";
    "origin=Debian,codename=${distro_codename}-security,label=Debian-Security";
};
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";
UEOF

cat > /etc/apt/apt.conf.d/20auto-upgrades <<'UEOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
UEOF

# ===========================================================================
# Interactive hostname prompt
# ===========================================================================
HOSTNAME_SET=0
if [[ -t 0 ]]; then
    CURRENT_HOSTNAME=$(hostname)
    echo
    read -rp "Enter hostname for this VPS [$CURRENT_HOSTNAME]: " NEW_HOSTNAME
    if [[ -n "$NEW_HOSTNAME" ]]; then
        hostnamectl set-hostname "$NEW_HOSTNAME"
        CURRENT_HOSTNAME="$NEW_HOSTNAME"
        HOSTNAME_SET=1
        echo "Hostname set to $CURRENT_HOSTNAME."
    else
        echo "Keeping hostname: $CURRENT_HOSTNAME"
    fi
fi

# ===========================================================================
# Done
# ===========================================================================
date > "$SENTINEL"
echo "==> VPS setup complete."
echo
if [[ "$HOSTNAME_SET" -eq 1 ]]; then
    echo "    Hostname: $CURRENT_HOSTNAME"
    echo
fi
echo "    +==========================================================+"
if [[ "$HOSTNAME_SET" -eq 0 ]]; then
    echo "    |  Set hostname so install.py activates the right config: |"
    echo "    |                                                        |"
    echo "    |  hostnamectl set-hostname wisp                           |"
    echo "    |                                                        |"
fi
echo "    |  Then clone and install:                                |"
echo "    |  git clone https://github.com/<you>/dotfiles.git        |"
echo "    |                                                        |"
echo "    |  cd dotfiles && cp per_host/wisp/.env.example \\          |"
echo "    |    per_host/wisp/.env   # then fill from Bitwarden      |"
echo "    |  python3 install.py                                     |"
echo "    +==========================================================+"
