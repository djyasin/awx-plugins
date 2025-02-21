from unittest import mock

import pytest

from awx_plugins.credentials import hashivault


def test_imported_azure_cloud_sdk_vars() -> None:
    from awx_plugins.credentials import azure_kv

    assert len(azure_kv.clouds) > 0
    assert all([hasattr(c, 'name') for c in azure_kv.clouds])
    assert all([hasattr(c, 'suffixes') for c in azure_kv.clouds])
    assert all([hasattr(c.suffixes, 'keyvault_dns') for c in azure_kv.clouds])


def test_hashivault_approle_auth() -> None:
    kwargs = {
        'role_id': 'the_role_id',
        'secret_id': 'the_secret_id',
    }
    expected_res = {
        'role_id': 'the_role_id',
        'secret_id': 'the_secret_id',
    }
    res = hashivault.approle_auth(**kwargs)
    assert res == expected_res


def test_hashivault_kubernetes_auth() -> None:
    kwargs = {
        'kubernetes_role': 'the_kubernetes_role',
    }
    expected_res = {
        'role': 'the_kubernetes_role',
        'jwt': 'the_jwt',
    }
    with mock.patch('pathlib.Path') as path_mock:
        mock.mock_open(path_mock.return_value.open, read_data='the_jwt')
        res = hashivault.kubernetes_auth(**kwargs)
        path_mock.assert_called_with(
            '/var/run/secrets/kubernetes.io/serviceaccount/token',
        )
        assert res == expected_res


def test_hashivault_client_cert_auth_explicit_role() -> None:
    kwargs = {
        'client_cert_role': 'test-cert-1',
    }
    expected_res = {
        'name': 'test-cert-1',
    }
    res = hashivault.client_cert_auth(**kwargs)
    assert res == expected_res


def test_hashivault_client_cert_auth_no_role() -> None:
    kwargs: dict[str, str] = {}
    expected_res = {
        'name': None,
    }
    res = hashivault.client_cert_auth(**kwargs)
    assert res == expected_res


def test_hashivault_userpass_auth() -> None:
    kwargs = {'username': 'the_username', 'password': 'the_password'}
    expected_res = {'username': 'the_username', 'password': 'the_password'}
    res = hashivault.userpass_auth(**kwargs)
    assert res == expected_res


def test_hashivault_handle_auth_token() -> None:
    kwargs = {
        'token': 'the_token',
    }
    token = hashivault.handle_auth(**kwargs)
    assert token == kwargs['token']


def test_hashivault_handle_auth_approle() -> None:
    kwargs = {
        'role_id': 'the_role_id',
        'secret_id': 'the_secret_id',
    }
    with mock.patch.object(hashivault, 'method_auth') as method_mock:
        method_mock.return_value = 'the_token'
        token = hashivault.handle_auth(**kwargs)
        method_mock.assert_called_with(**kwargs, auth_param=kwargs)
        assert token == 'the_token'


def test_hashivault_handle_auth_kubernetes() -> None:
    kwargs = {
        'kubernetes_role': 'the_kubernetes_role',
    }
    with mock.patch.object(hashivault, 'method_auth') as method_mock:
        with mock.patch('pathlib.Path') as path_mock:
            mock.mock_open(path_mock.return_value.open, read_data='the_jwt')
            method_mock.return_value = 'the_token'
            token = hashivault.handle_auth(**kwargs)
            method_mock.assert_called_with(
                **kwargs,
                auth_param={
                    'role': 'the_kubernetes_role',
                    'jwt': 'the_jwt',
                },
            )
            assert token == 'the_token'


def test_hashivault_handle_auth_client_cert() -> None:
    kwargs = {
        'client_cert_public': 'foo',
        'client_cert_private': 'bar',
        'client_cert_role': 'test-cert-1',
    }
    auth_params = {
        'name': 'test-cert-1',
    }
    with mock.patch.object(hashivault, 'method_auth') as method_mock:
        method_mock.return_value = 'the_token'
        token = hashivault.handle_auth(**kwargs)
        method_mock.assert_called_with(**kwargs, auth_param=auth_params)
        assert token == 'the_token'


def test_hashivault_handle_auth_not_enough_args() -> None:
    with pytest.raises(Exception):
        hashivault.handle_auth()


class TestDelineaImports:
    """These module have a try-except for ImportError which will allow using
    the older library but we do not want the awx_devel image to have the older
    library, so these tests are designed to fail if these wind up using the
    fallback import."""

    def test_dsv_import(self) -> None:
        from awx_plugins.credentials.dsv import SecretsVault  # noqa
        # assert this module as opposed to older thycotic.secrets.vault
        assert SecretsVault.__module__ == 'delinea.secrets.vault'

    def test_tss_import(self) -> None:
        from awx_plugins.credentials.tss import DomainPasswordGrantAuthorizer, PasswordGrantAuthorizer, SecretServer, ServerSecret  # noqa

        for cls in (
                DomainPasswordGrantAuthorizer,
                PasswordGrantAuthorizer,
                SecretServer,
                ServerSecret,
        ):
            # assert this module as opposed to older thycotic.secrets.server
            assert cls.__module__ == 'delinea.secrets.server'
