"""Which OpenStack credentials a provider authenticates with.

The provider reads credentials from its config dict and, failing that, from
the ``OS_*`` environment. These tests pin the precedence between the two:
credentials configured explicitly win over whatever happens to be in the
process environment, so a provider built for one identity never signs in as
another. Nothing here touches a network: the Keystone version probe is
patched and keystoneauth plugins are plain objects until used.
"""

import os
import unittest
from unittest import mock

from keystoneauth1.identity import v3

from cloudbridge.providers.openstack.provider import OpenStackCloudProvider

AUTH_URL = 'https://keystone.example.org:5000/v3'

PASSWORD_ENV = {
    'OS_USERNAME': 'ambient-user',
    'OS_PASSWORD': 'ambient-password',
    'OS_PROJECT_NAME': 'ambient-project',
}

APP_CRED_ENV = {
    'OS_APPLICATION_CREDENTIAL_ID': 'ambient-app-cred-id',
    'OS_APPLICATION_CREDENTIAL_SECRET': 'ambient-app-cred-secret',
}

ALL_CREDENTIAL_VARS = tuple(PASSWORD_ENV) + tuple(APP_CRED_ENV)


def _environment(**values):
    """The process environment with only the given OS_* credentials set."""
    env = {k: v for k, v in os.environ.items() if k not in ALL_CREDENTIAL_VARS}
    env.update(values)
    return mock.patch.dict(os.environ, env, clear=True)


def _provider(**config):
    # A configured zone keeps the compute service from asking Nova for one
    # while the provider is being built.
    return OpenStackCloudProvider(
        dict(config, os_auth_url=AUTH_URL, os_zone_name='nova'))


def _keystone_auth(provider):
    with mock.patch.object(OpenStackCloudProvider, '_keystone_version',
                           new_callable=mock.PropertyMock, return_value=3):
        # pylint:disable=protected-access
        return provider._keystone_session.auth


class OpenStackCredentialPrecedenceTestCase(unittest.TestCase):

    def test_configured_application_credential_ignores_ambient_password(self):
        # The process may carry the server's own OS_USERNAME/OS_PASSWORD; a
        # provider configured with an application credential must use that
        # credential, not the ambient identity.
        with _environment(**PASSWORD_ENV):
            provider = _provider(
                os_application_credential_id='configured-id',
                os_application_credential_secret='configured-secret')
            self.assertIsNone(provider.username)
            self.assertIsNone(provider.password)
            auth = _keystone_auth(provider)
        self.assertIsInstance(auth, v3.ApplicationCredential)
        self.assertEqual(auth.auth_methods[0].application_credential_id,
                         'configured-id')

    def test_configured_password_ignores_ambient_application_credential(self):
        with _environment(**APP_CRED_ENV):
            provider = _provider(os_username='configured-user',
                                 os_password='configured-password',
                                 os_project_name='configured-project')
            self.assertIsNone(provider.app_cred_id)
            self.assertIsNone(provider.app_cred_secret)
            auth = _keystone_auth(provider)
        self.assertIsInstance(auth, v3.Password)
        self.assertEqual(auth.auth_methods[0].username, 'configured-user')

    def test_environment_is_used_when_nothing_is_configured(self):
        with _environment(**PASSWORD_ENV):
            provider = _provider()
            self.assertEqual(provider.username, 'ambient-user')
            self.assertEqual(provider.password, 'ambient-password')
            auth = _keystone_auth(provider)
        self.assertIsInstance(auth, v3.Password)

    def test_environment_completes_a_partially_configured_credential(self):
        # Keeping the secret out of the config file and in the environment is
        # legitimate: the environment fills in the missing half of the set
        # that is configured, and only that set.
        with _environment(**PASSWORD_ENV, **APP_CRED_ENV):
            provider = _provider(os_username='configured-user')
            self.assertEqual(provider.username, 'configured-user')
            self.assertEqual(provider.password, 'ambient-password')
            self.assertIsNone(provider.app_cred_id)
            self.assertIsNone(provider.app_cred_secret)

        with _environment(**PASSWORD_ENV, **APP_CRED_ENV):
            provider = _provider(os_application_credential_id='configured-id')
            self.assertEqual(provider.app_cred_id, 'configured-id')
            self.assertEqual(provider.app_cred_secret,
                             'ambient-app-cred-secret')
            self.assertIsNone(provider.username)
            self.assertIsNone(provider.password)
