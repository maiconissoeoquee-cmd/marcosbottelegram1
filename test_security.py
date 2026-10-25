from app.security.secrets import looks_like_secret, redact
from app.security.url_guard import check_url


def test_bloqueia_esquemas_perigosos():
    for url in ["javascript:alert(1)", "file:///etc/passwd", "ftp://example.com/x"]:
        assert check_url(url)[0] is False


def test_bloqueia_http_por_padrao():
    assert check_url("http://example.com")[0] is False


def test_bloqueia_hosts_locais_e_privados():
    for url in ["https://localhost/x", "https://127.0.0.1/x", "https://10.0.0.5/x",
                "https://192.168.1.1/x", "https://169.254.169.254/latest", "https://app.local/x"]:
        assert check_url(url)[0] is False, url


def test_bloqueia_credenciais_na_url():
    assert check_url("https://user:senha@example.com/x")[0] is False


def test_aceita_https_publico():
    assert check_url("https://play.google.com/store/apps/details?id=com.kiloo.subwaysurf")[0] is True


def test_detecta_chave_e_token_sem_mostrar_valor():
    fake_key = "sk-" + "a" * 30
    fake_token = "123456789:" + "B" * 35
    assert looks_like_secret("minha chave " + fake_key)
    assert looks_like_secret("token " + fake_token)
    assert not looks_like_secret("me manda o Subway Surfers")
    assert fake_key not in redact(fake_key, [fake_key])
