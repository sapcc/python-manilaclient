#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from unittest import mock

import ddt

from manilaclient import api_versions
from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v2 import fakes
from manilaclient.v2 import share_server_replicas

FAKE_REPLICA = 'fake_replica_id'


@ddt.ddt
class ShareServerReplicasTest(utils.TestCase):
    class _FakeShareServerReplica:
        id = 'fake_share_server_replica_id'

    def setUp(self):
        super().setUp()
        microversion = api_versions.APIVersion("2.100")
        self.manager = share_server_replicas.ShareServerReplicaManager(
            fakes.FakeClient(api_version=microversion)
        )

    def test_get(self):
        with mock.patch.object(self.manager, '_get', mock.Mock()):
            self.manager.get(FAKE_REPLICA)
            self.manager._get.assert_called_once_with(
                share_server_replicas.RESOURCE_PATH % FAKE_REPLICA,
                share_server_replicas.RESOURCE_NAME,
            )

    def test_get_with_object(self):
        replica = self._FakeShareServerReplica
        with mock.patch.object(self.manager, '_get', mock.Mock()):
            self.manager.get(replica)
            self.manager._get.assert_called_once_with(
                share_server_replicas.RESOURCE_PATH % replica.id,
                share_server_replicas.RESOURCE_NAME,
            )

    def test_list(self):
        with mock.patch.object(self.manager, '_list', mock.Mock()):
            self.manager.list()
            self.manager._list.assert_called_once_with(
                share_server_replicas.RESOURCES_PATH + '/detail',
                share_server_replicas.RESOURCES_NAME,
            )

    def test_list_with_share_server(self):
        share_server = 'fake_server_id'
        with mock.patch.object(self.manager, '_list', mock.Mock()):
            self.manager.list(share_server=share_server)
            self.manager._list.assert_called_once_with(
                share_server_replicas.RESOURCES_PATH
                + '/detail'
                + '?share_server_id=fake_server_id',
                share_server_replicas.RESOURCES_NAME,
            )

    def test_list_with_search_opts(self):
        search_opts = {'status': 'active'}
        with mock.patch.object(self.manager, '_list', mock.Mock()):
            self.manager.list(search_opts=search_opts)
            self.manager._list.assert_called_once_with(
                share_server_replicas.RESOURCES_PATH
                + '/detail'
                + '?status=active',
                share_server_replicas.RESOURCES_NAME,
            )

    def test_create(self):
        values = {
            'share_server': 'fake_server_id',
            'availability_zone': 'az1',
        }
        with mock.patch.object(self.manager, '_create', fakes.fake_create):
            result = self.manager.create(**values)
            expected_body = {
                share_server_replicas.RESOURCE_NAME: {
                    'share_server_id': 'fake_server_id',
                    'availability_zone': 'az1',
                }
            }
            self.assertEqual(
                share_server_replicas.RESOURCES_PATH, result['url']
            )
            self.assertEqual(
                share_server_replicas.RESOURCE_NAME, result['resp_key']
            )
            self.assertEqual(expected_body, result['body'])

    def test_create_with_metadata(self):
        values = {
            'share_server': 'fake_server_id',
            'metadata': {'key': 'value'},
        }
        with mock.patch.object(self.manager, '_create', fakes.fake_create):
            result = self.manager.create(**values)
            expected_body = {
                share_server_replicas.RESOURCE_NAME: {
                    'share_server_id': 'fake_server_id',
                    'metadata': {'key': 'value'},
                }
            }
            self.assertEqual(expected_body, result['body'])

    def test_create_with_share_network(self):
        values = {
            'share_server': 'fake_server_id',
            'share_network': 'fake_share_network_id',
        }
        with mock.patch.object(self.manager, '_create', fakes.fake_create):
            result = self.manager.create(**values)
            expected_body = {
                share_server_replicas.RESOURCE_NAME: {
                    'share_server_id': 'fake_server_id',
                    'share_network_id': 'fake_share_network_id',
                }
            }
            self.assertEqual(expected_body, result['body'])

    def test_create_with_metadata_from_create_arg(self):
        values = {
            'share_server': 'fake_server_id',
            'metadata': {'key': 'value'},
        }
        with mock.patch.object(self.manager, '_create', fakes.fake_create):
            result = self.manager.create(**values)
            expected_body = {
                share_server_replicas.RESOURCE_NAME: {
                    'share_server_id': 'fake_server_id',
                    'metadata': {'key': 'value'},
                }
            }
            self.assertEqual(expected_body, result['body'])

    def test_delete_str(self):
        with mock.patch.object(self.manager, '_delete', mock.Mock()):
            self.manager.delete(FAKE_REPLICA)
            self.manager._delete.assert_called_once_with(
                share_server_replicas.RESOURCE_PATH % FAKE_REPLICA
            )

    def test_delete_with_force(self):
        with mock.patch.object(self.manager, '_action', mock.Mock()):
            self.manager.delete(FAKE_REPLICA, force=True)
            self.manager._action.assert_called_once_with(
                'force_delete', FAKE_REPLICA
            )

    def test_promote(self):
        with mock.patch.object(self.manager, '_action', mock.Mock()):
            self.manager.promote(FAKE_REPLICA)
            self.manager._action.assert_called_once_with(
                'promote', FAKE_REPLICA
            )

    def test_resync(self):
        with mock.patch.object(self.manager, '_action', mock.Mock()):
            self.manager.resync(FAKE_REPLICA)
            self.manager._action.assert_called_once_with(
                'resync', FAKE_REPLICA
            )

    def test_reset_replica_state(self):
        replica_state = 'in_sync'
        with mock.patch.object(self.manager, '_action', mock.Mock()):
            self.manager.reset_replica_state(FAKE_REPLICA, replica_state)
            self.manager._action.assert_called_once_with(
                'reset_replica_state',
                FAKE_REPLICA,
                {'replica_state': replica_state},
            )

    def test_reset_status(self):
        status = 'available'
        with mock.patch.object(self.manager, '_action', mock.Mock()):
            self.manager.reset_status(FAKE_REPLICA, status)
            self.manager._action.assert_called_once_with(
                'reset_status',
                FAKE_REPLICA,
                {'status': status},
            )

    def test_get_metadata(self):
        with mock.patch.object(
            self.manager, 'get_metadata', mock.Mock()
        ) as mock_get:
            self.manager.get_metadata(FAKE_REPLICA)
            mock_get.assert_called_once()

    def test_set_metadata(self):
        with mock.patch.object(
            self.manager, 'set_metadata', mock.Mock()
        ) as mock_set:
            metadata = {'key': 'value'}
            self.manager.set_metadata(FAKE_REPLICA, metadata)
            mock_set.assert_called_once()

    def test_delete_metadata(self):
        with mock.patch.object(
            self.manager, 'delete_metadata', mock.Mock()
        ) as mock_delete:
            keys = ['key1', 'key2']
            self.manager.delete_metadata(FAKE_REPLICA, keys)
            mock_delete.assert_called_once()

    def test_update_all_metadata(self):
        with mock.patch.object(
            self.manager, 'update_all_metadata', mock.Mock()
        ) as mock_update:
            metadata = {'key': 'value'}
            self.manager.update_all_metadata(FAKE_REPLICA, metadata)
            mock_update.assert_called_once()
