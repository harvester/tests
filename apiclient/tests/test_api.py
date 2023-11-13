from unittest import TestCase, mock

import requests

from harvester_api.api import HarvesterAPI


class TestHarvesterAPI(TestCase):

    def test_init_full_customized(self):
        endpoint = "https://endpoint/"
        token = "the_fake:token"

        mock_session = mock.Mock(requests.Session())
        api = HarvesterAPI(endpoint, token, mock_session)

        self.assertEqual(api.endpoint, endpoint)
        self.assertEqual(api.session, mock_session)
        mock_session.headers.update.assert_called_with(Authorization=token)
        # customized session will not mount retries
        mock_session.mount.assert_not_called()

    def test_init_default(self):
        endpoint = "https://endpoint/"

        api = HarvesterAPI(endpoint)

        self.assertEqual(api.endpoint, endpoint)
        self.assertIsInstance(api.session, requests.Session)
        self.assertIn(("Authorization", ""), api.session.headers.items())

        with mock.patch('requests.Session') as m_session:
            api = HarvesterAPI(endpoint)

            m_session.assert_called()
            m_session().mount.assert_called()

    def test_set_retries_default(self):
        defaults = dict(total=5,
                        status_forcelist=(500, 502, 504),
                        backoff_factor=10.0)

        api = HarvesterAPI("https://endpoint/")
        session = api.session

        for prefix in ("http://", "https://"):
            with self.subTest(prefix=prefix):
                self.assertIn(prefix, session.adapters)

                retries = session.get_adapter(prefix).max_retries

                for attr, val in defaults.items():
                    with self.subTest(attr=attr, val=val):
                        self.assertEqual(getattr(retries, attr), val)

    def test_set_retries_customized(self):
        api = HarvesterAPI("https://endpoint/")
        session = api.session

        updates = dict(total=10,
                       status_forcelist=[400, 404],
                       backoff_factor=5)

        api.set_retries(**updates)

        for prefix in ("http://", "https://"):
            retries = session.get_adapter(prefix).max_retries

            for attr, val in updates.items():
                with self.subTest(attr=attr, val=val):
                    self.assertEqual(getattr(retries, attr), val)

    def test_load_managers(self):
        default_ver, base_ver, new_ver = "", "0.0.0", "v1.1.0"
        api = HarvesterAPI("https://endpoint")

        self.assertEqual(api.hosts.support_to, base_ver)
        self.assertEqual(api.hosts._ver, default_ver)

        api.load_managers(new_ver)
        self.assertTrue(api.hosts.is_support(new_ver))
        self.assertEqual(api.hosts._ver, new_ver)

    def test_authenticate(self):
        user, pwd, token = "testuser", "testpasswd", "fake:token"
        post_json = dict(username=user, password=pwd)

        api = HarvesterAPI("https://endpoint/")

        m_resp = mock.MagicMock()
        m_resp.configure_mock(**{"status_code": 201,
                              "json.return_value": dict(token=token)})
        with mock.patch.object(api, '_post', return_value=m_resp) as m_post:
            resp = api.authenticate(user, pwd)

            m_post.assert_called()
            self.assertDictEqual(m_post.call_args.kwargs, dict(json=post_json))

            m_resp.json.assert_called()
            self.assertEqual(f"Bearer {token}", api.session.headers['Authorization'])
            self.assertDictEqual(resp, m_resp.json.return_value)

        m_post.reset_mock(), m_resp.reset_mock()
        with mock.patch.object(api, '_post', return_value=m_resp) as m_post:
            other_kws = dict(verify=False, some="thing")
            resp = api.authenticate(user, pwd, **other_kws)

            m_post.assert_called()
            self.assertDictEqual(m_post.call_args.kwargs, dict(json=post_json, **other_kws))

    def test_login(self):
        endpoint, user, pwd = "https://endpoint", "testuser", "testpasswd"
        fake_version = "8.8.8"

        with mock.patch.object(HarvesterAPI, 'authenticate') as m_auth, \
             mock.patch.object(HarvesterAPI, 'cluster_version') as m_cluster_version:
            m_cluster_version.return_value = fake_version

            api = HarvesterAPI.login(endpoint, user, pwd)

            m_auth.assert_called_once_with(user, pwd, verify=True)
            self.assertEqual(api.vms._ver, m_cluster_version)

        m_session, ssl_verify = mock.MagicMock(), False
        with mock.patch.object(HarvesterAPI, 'authenticate') as m_auth, \
             mock.patch.object(HarvesterAPI, 'cluster_version') as m_cluster_version:
            api = HarvesterAPI.login(endpoint, user, pwd, m_session, ssl_verify=ssl_verify)

            self.assertEqual(api.session, m_session)
            m_auth.assert_called_once_with(user, pwd, verify=ssl_verify)
