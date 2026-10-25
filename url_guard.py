"""Validação de URLs: bloqueia esquemas perigosos, hosts locais e IPs privados (anti-SSRF)."""
import ipaddress
import socket
from urllib.parse import urlparse

BLOCKED_HOSTNAMES = {"localhost", "localhost.localdomain", "metadata.google.internal"}


def check_url(url: str, allow_http: bool = False) -> tuple[bool, str]:
    if not url or len(url) > 2048:
        return False, "URL vazia ou longa demais"
    p = urlparse(url.strip())
    allowed = {"https", "http"} if allow_http else {"https"}
    if p.scheme.lower() not in allowed:
        return False, f"esquema não permitido: {p.scheme or 'vazio'}"
    if not p.hostname:
        return False, "sem host"
    if p.username or p.password:
        return False, "credenciais na URL não são permitidas"
    host = p.hostname.lower()
    if host in BLOCKED_HOSTNAMES or host.endswith(".local") or host.endswith(".internal"):
        return False, "host local"
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return True, "ok"
    if not ip.is_global:
        return False, "endereço IP privado ou local"
    return True, "ok"


def resolves_to_public_ip(host: str) -> bool:
    """Confirma via DNS que o host só aponta para IPs públicos (evita DNS apontando para a rede interna)."""
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return False
    if not infos:
        return False
    return all(ipaddress.ip_address(i[4][0]).is_global for i in infos)
