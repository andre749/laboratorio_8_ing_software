"""Unit tests for BrokerSettings and build_connection_parameters."""

import os
from unittest.mock import patch

import pika

from shared.messaging.topology import BrokerSettings, build_connection_parameters


class TestBrokerSettingsFromEnv:
    def test_reads_values_from_environment(self):
        env = {
            "RABBITMQ_HOST": "myhost",
            "RABBITMQ_PORT": "5673",
            "RABBITMQ_USER": "admin",
            "RABBITMQ_PASSWORD": "secret",
            "RABBITMQ_VHOST": "/test",
        }
        with patch.dict(os.environ, env, clear=False):
            settings = BrokerSettings.from_env()
        assert settings.host == "myhost"
        assert settings.port == 5673
        assert settings.user == "admin"
        assert settings.password == "secret"
        assert settings.virtual_host == "/test"

    def test_falls_back_to_defaults_when_env_not_set(self):
        keys = ["RABBITMQ_HOST", "RABBITMQ_PORT", "RABBITMQ_USER", "RABBITMQ_PASSWORD", "RABBITMQ_VHOST"]
        env_without = {k: "" for k in keys}
        with patch.dict(os.environ, {}, clear=False):
            for k in keys:
                os.environ.pop(k, None)
            settings = BrokerSettings.from_env()
        assert settings.host == "localhost"
        assert settings.port == 5672
        assert settings.user == "students"
        assert settings.virtual_host == "/"


class TestBuildConnectionParameters:
    def test_returns_pika_connection_parameters(self):
        settings = BrokerSettings(
            host="myhost",
            port=5672,
            user="user",
            password="pass",
            virtual_host="/",
        )
        params = build_connection_parameters(settings)
        assert isinstance(params, pika.ConnectionParameters)
        assert params.host == "myhost"
        assert params.port == 5672
        assert params.virtual_host == "/"
