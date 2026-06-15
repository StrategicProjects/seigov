"""Testes de configuração (offline)."""

from seigov import SeiConfig, SipConfig


def test_sei_config_defaults_genericos():
    cfg = SeiConfig(sigla_sistema="X", identificacao_servico="Y")
    # sem URL embutida: serve a qualquer instalacao do SEI
    assert cfg.url == ""
    assert cfg.sigla_sistema == "X"
    assert cfg.identificacao_servico == "Y"


def test_sei_config_url_configuravel():
    cfg = SeiConfig(url="https://sei.exemplo.gov.br/sei/ws/SeiWS.php")
    assert cfg.url.endswith("SeiWS.php")


def test_sei_config_resolve_env(monkeypatch):
    monkeypatch.setenv("SEIGOV_URL", "https://sei.env.gov.br/ws")
    monkeypatch.setenv("SEIGOV_SIGLA_SISTEMA", "ENVSYS")
    cfg = SeiConfig()
    assert cfg.url == "https://sei.env.gov.br/ws"
    assert cfg.sigla_sistema == "ENVSYS"


def test_sip_config_env(monkeypatch):
    monkeypatch.setenv("SEIGOV_SIP_CHAVE_ACESSO", "abc")
    cfg = SipConfig()
    assert cfg.chave_acesso == "abc"
    assert cfg.url == ""
