#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#
from unittest import mock

from osc_lib import exceptions

from manilaclient.osc.v2 import share_server_replicas as osc_ss_replicas
from manilaclient.tests.unit.osc import osc_fakes
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestShareServerReplica(manila_fakes.TestShare):
    def setUp(self):
        super().setUp()

        self.replicas_mock = (
            self.app.client_manager.share.share_server_replicas
        )
        self.replicas_mock.reset_mock()


class TestShareServerReplicaList(TestShareServerReplica):
    columns = [
        'id',
        'source_share_server_id',
        'status',
        'replica_state',
        'host',
        'availability_zone',
    ]

    def setUp(self):
        super().setUp()

        self.replica = osc_fakes.FakeResource(
            info={
                'id': 'share-server-replica-id',
                'source_share_server_id': 'source-server-id',
                'status': 'available',
                'replica_state': 'in_sync',
                'host': 'fake_host@backend#pool',
                'availability_zone': 'az1',
            },
            loaded=True,
        )
        self.replicas_mock.list.return_value = [self.replica]

        self.cmd = osc_ss_replicas.ListShareServerReplica(self.app, None)

    def test_list(self):
        arglist = []
        verifylist = [
            ('share_server', None),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.replicas_mock.list.assert_called_once_with(share_server=None)

        self.assertEqual(
            [
                'ID',
                'Source Share Server ID',
                'Status',
                'Replica State',
                'Host',
                'Availability Zone',
            ],
            columns,
        )

        self.assertEqual(
            [
                (
                    'share-server-replica-id',
                    'source-server-id',
                    'available',
                    'in_sync',
                    'fake_host@backend#pool',
                    'az1',
                )
            ],
            list(data),
        )


class TestShareServerReplicaShow(TestShareServerReplica):
    def setUp(self):
        super().setUp()

        self.replica = osc_fakes.FakeResource(
            info={
                'id': 'share-server-replica-id',
                'status': 'available',
                'replica_state': 'in_sync',
                'availability_zone': 'az1',
                'links': [{'href': 'http://example.com'}],
            },
            loaded=True,
        )
        self.replicas_mock.get.return_value = self.replica

        self.cmd = osc_ss_replicas.ShowShareServerReplica(self.app, None)

    def test_show(self):
        arglist = [self.replica.id]
        verifylist = [
            ('replica', self.replica.id),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.replicas_mock.get.assert_called_once_with(self.replica.id)

        result = dict(zip(columns, data))
        self.assertEqual('share-server-replica-id', result['id'])
        self.assertEqual('az1', result['availability_zone'])
        self.assertNotIn('links', result)


class TestShareServerReplicaSet(TestShareServerReplica):
    def setUp(self):
        super().setUp()

        self.share_server_replica = osc_fakes.FakeResource(
            info={"id": "share-server-replica-id"},
            methods={"set_metadata": None},
            loaded=True,
        )
        self.replicas_mock.get.return_value = self.share_server_replica

        self.cmd = osc_ss_replicas.SetShareServerReplica(self.app, None)

    def test_set_replica_state(self):
        arglist = [
            self.share_server_replica.id,
            '--replica-state',
            'in_sync',
        ]
        verifylist = [
            ('replica', self.share_server_replica.id),
            ('replica_state', 'in_sync'),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.replicas_mock.reset_replica_state.assert_called_once_with(
            self.share_server_replica, 'in_sync'
        )
        self.assertIsNone(result)

    def test_set_property(self):
        arglist = [
            self.share_server_replica.id,
            '--property',
            'test_key=test_value',
        ]
        verifylist = [
            ('replica', self.share_server_replica.id),
            ('property', {'test_key': 'test_value'}),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        self.share_server_replica.set_metadata.assert_called_once_with(
            {'test_key': 'test_value'}
        )

    def test_set_status(self):
        arglist = [
            self.share_server_replica.id,
            '--status',
            'active',
        ]
        verifylist = [
            ('replica', self.share_server_replica.id),
            ('status', 'active'),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.replicas_mock.reset_status.assert_called_once_with(
            self.share_server_replica, 'active'
        )
        self.assertIsNone(result)

    def test_set_status_invalid_value(self):
        arglist = [
            self.share_server_replica.id,
            '--status',
            'invalid_status',
        ]
        verifylist = [
            ('replica', self.share_server_replica.id),
            ('status', 'invalid_status'),
        ]

        self.assertRaises(
            manila_fakes.osc_utils.ParserException,
            self.check_parser,
            self.cmd,
            arglist,
            verifylist,
        )

    def test_set_property_exception(self):
        arglist = [
            self.share_server_replica.id,
            '--property',
            'test_key=test_value',
        ]
        verifylist = [
            ('replica', self.share_server_replica.id),
            ('property', {'test_key': 'test_value'}),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.share_server_replica.set_metadata.side_effect = (
            exceptions.BadRequest
        )
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args
        )

    def test_set_without_any_option(self):
        arglist = [self.share_server_replica.id]
        verifylist = [
            ('replica', self.share_server_replica.id),
            ('replica_state', None),
            ('status', None),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args
        )


class TestShareServerReplicaUnset(TestShareServerReplica):
    def setUp(self):
        super().setUp()

        self.share_server_replica = osc_fakes.FakeResource(
            info={"id": "share-server-replica-id"},
            methods={"delete_metadata": None},
            loaded=True,
        )
        self.replicas_mock.get.return_value = self.share_server_replica

        self.cmd = osc_ss_replicas.UnsetShareServerReplica(self.app, None)

    def test_unset_property(self):
        arglist = [
            "--property",
            "test_key",
            self.share_server_replica.id,
        ]
        verifylist = [
            ("property", ["test_key"]),
            ("replica", self.share_server_replica.id),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        self.share_server_replica.delete_metadata.assert_called_once_with(
            ["test_key"]
        )

    def test_unset_multiple_properties(self):
        arglist = [
            "--property",
            "key1",
            "--property",
            "key2",
            self.share_server_replica.id,
        ]
        verifylist = [
            ("property", ["key1", "key2"]),
            ("replica", self.share_server_replica.id),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        expected_calls = [mock.call(["key1"]), mock.call(["key2"])]
        self.share_server_replica.delete_metadata.assert_has_calls(
            expected_calls, any_order=False
        )
        self.assertEqual(
            self.share_server_replica.delete_metadata.call_count, 2
        )

    def test_unset_property_exception(self):
        arglist = [
            "--property",
            "test_key",
            self.share_server_replica.id,
        ]
        verifylist = [
            ("property", ["test_key"]),
            ("replica", self.share_server_replica.id),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.share_server_replica.delete_metadata.side_effect = (
            exceptions.NotFound
        )
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args
        )

    def test_unset_without_property(self):
        arglist = [self.share_server_replica.id]
        verifylist = [
            ("property", None),
            ("replica", self.share_server_replica.id),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args
        )


class TestShareServerReplicaCreate(TestShareServerReplica):
    def setUp(self):
        super().setUp()

        self.share_servers_mock = self.app.client_manager.share.share_servers
        self.share_servers_mock.reset_mock()
        self.share_networks_mock = self.app.client_manager.share.share_networks
        self.share_networks_mock.reset_mock()

        self.share_server = osc_fakes.FakeResource(
            info={
                'id': 'source-server-id',
            },
            loaded=True,
        )
        self.share_servers_mock.get.return_value = self.share_server

        self.share_network = osc_fakes.FakeResource(
            info={
                'id': 'share-network-id',
            },
            loaded=True,
        )
        self.share_networks_mock.get.return_value = self.share_network

        self.replica = osc_fakes.FakeResource(
            info={
                'id': 'share-server-replica-id',
                'source_share_server_id': 'source-server-id',
                'status': 'creating',
                'replica_state': 'in_sync',
                'availability_zone': 'az2',
                'links': [{'href': 'http://example.com'}],
            },
            loaded=True,
        )
        self.replicas_mock.create.return_value = self.replica
        self.replicas_mock.get.return_value = self.replica

        self.cmd = osc_ss_replicas.CreateShareServerReplica(self.app, None)

    def test_create(self):
        arglist = [self.share_server.id]
        verifylist = [
            ('share_server', self.share_server.id),
            ('availability_zone', None),
            ('wait', False),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.replicas_mock.create.assert_called_once_with(
            share_server=self.share_server
        )
        result = dict(zip(columns, data))
        self.assertEqual(self.replica.id, result['id'])
        self.assertNotIn('links', result)

    def test_create_with_az_and_property(self):
        arglist = [
            self.share_server.id,
            '--availability-zone',
            'az2',
            '--property',
            'test_key=test_value',
        ]
        verifylist = [
            ('share_server', self.share_server.id),
            ('availability_zone', 'az2'),
            ('property', {'test_key': 'test_value'}),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        self.replicas_mock.create.assert_called_once_with(
            share_server=self.share_server,
            availability_zone='az2',
            metadata={'test_key': 'test_value'},
        )

    def test_create_with_share_network(self):
        arglist = [
            self.share_server.id,
            '--share-network',
            self.share_network.id,
        ]
        verifylist = [
            ('share_server', self.share_server.id),
            ('share_network', self.share_network.id),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        self.replicas_mock.create.assert_called_once_with(
            share_server=self.share_server,
            share_network=self.share_network.id,
        )

    def test_create_wait(self):
        arglist = [self.share_server.id, '--wait']
        verifylist = [
            ('share_server', self.share_server.id),
            ('wait', True),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch(
            'osc_lib.utils.wait_for_status', return_value=True
        ) as wait_mock:
            self.cmd.take_action(parsed_args)

        wait_mock.assert_called_once_with(
            status_f=self.replicas_mock.get,
            res_id=self.replica.id,
            success_status=['inactive'],
        )

        self.replicas_mock.get.assert_called_once_with(self.replica.id)


class TestShareServerReplicaDelete(TestShareServerReplica):
    def setUp(self):
        super().setUp()

        self.cmd = osc_ss_replicas.DeleteShareServerReplica(self.app, None)
        self.replica_id = 'share-server-replica-id'

    def test_delete(self):
        arglist = [self.replica_id]
        verifylist = [
            ('replica', [self.replica_id]),
            ('force', False),
            ('wait', False),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.replicas_mock.delete.assert_called_once_with(
            self.replica_id, force=False
        )
        self.assertIsNone(result)

    def test_delete_force_wait(self):
        arglist = [self.replica_id, '--force', '--wait']
        verifylist = [
            ('replica', [self.replica_id]),
            ('force', True),
            ('wait', True),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=True):
            result = self.cmd.take_action(parsed_args)

        self.replicas_mock.delete.assert_called_once_with(
            self.replica_id, force=True
        )
        self.assertIsNone(result)

    def test_delete_wait_error(self):
        arglist = [self.replica_id, '--wait']
        verifylist = [
            ('replica', [self.replica_id]),
            ('force', False),
            ('wait', True),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=False):
            self.assertRaises(
                exceptions.CommandError, self.cmd.take_action, parsed_args
            )


class TestShareServerReplicaPromote(TestShareServerReplica):
    def setUp(self):
        super().setUp()

        self.replica = osc_fakes.FakeResource(
            info={'id': 'share-server-replica-id'}, loaded=True
        )
        self.replicas_mock.get.return_value = self.replica

        self.cmd = osc_ss_replicas.PromoteShareServerReplica(self.app, None)

    def test_promote(self):
        arglist = [self.replica.id]
        verifylist = [
            ('replica', self.replica.id),
            ('wait', False),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.replicas_mock.promote.assert_called_once_with(self.replica)
        self.assertIsNone(result)

    def test_promote_wait(self):
        arglist = [self.replica.id, '--wait']
        verifylist = [
            ('replica', self.replica.id),
            ('wait', True),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_status', return_value=True):
            result = self.cmd.take_action(parsed_args)

        self.replicas_mock.promote.assert_called_once_with(self.replica)
        self.assertIsNone(result)

    def test_promote_error(self):
        arglist = [self.replica.id]
        verifylist = [
            ('replica', self.replica.id),
            ('wait', False),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.replicas_mock.promote.side_effect = Exception('boom')
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args
        )


class TestShareServerReplicaResync(TestShareServerReplica):
    def setUp(self):
        super().setUp()

        self.replica = osc_fakes.FakeResource(
            info={'id': 'share-server-replica-id'}, loaded=True
        )
        self.replicas_mock.get.return_value = self.replica

        self.cmd = osc_ss_replicas.ResyncShareServerReplica(self.app, None)

    def test_resync(self):
        arglist = [self.replica.id]
        verifylist = [
            ('replica', self.replica.id),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.replicas_mock.resync.assert_called_once_with(self.replica)
        self.assertIsNone(result)

    def test_resync_error(self):
        arglist = [self.replica.id]
        verifylist = [
            ('replica', self.replica.id),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.replicas_mock.resync.side_effect = Exception('boom')
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args
        )
