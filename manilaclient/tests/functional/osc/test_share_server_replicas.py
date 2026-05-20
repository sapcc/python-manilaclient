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

import ast
import json

from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as tempest_exc

from manilaclient import config
from manilaclient.tests.functional.osc import base
from manilaclient.tests.functional import utils

CONF = config.CONF


@utils.skip_if_microversion_not_supported('2.100')
class ShareServerReplicasCLITest(base.OSCClientTestBase):
    def setUp(self):
        super().setUp()
        # Share server replicas are admin-only operations
        self.client = self.admin_client

    def _get_two_availability_zones(self):
        def _parse_caps(value):
            if isinstance(value, dict):
                return value
            for parser in (ast.literal_eval, json.loads):
                try:
                    parsed = parser(value)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    continue
            return {}

        azs = self.listing_result('share', 'availability zone list')
        available_azs = {az.get('Name') for az in azs if az.get('Name')}

        pools = json.loads(
            self.openstack(
                'share pool list --detail -f json', client=self.client
            )
        )
        services = json.loads(
            self.openstack('share service list -f json', client=self.client)
        )

        backend_domains = {}
        for pool in pools:
            backend = pool.get('Backend')
            if not backend:
                name = pool.get('Name', '')
                backend = (
                    name.split('@', 1)[1].split('#', 1)[0]
                    if isinstance(name, str) and '@' in name
                    else None
                )
            caps = _parse_caps(pool.get('Capabilities'))
            domain = caps.get('replication_domain')
            if (
                backend
                and caps.get('driver_handles_share_servers') is True
                and domain not in (None, '', 'None')
            ):
                backend_domains.setdefault(backend, set()).add(str(domain))

        backend_to_zones = {}
        for service in services:
            host = service.get('Host', '')
            zone = service.get('Zone') or service.get('Availability Zone')
            if '@' in host and zone in available_azs:
                backend = host.split('@', 1)[1].split('#', 1)[0]
                backend_to_zones.setdefault(backend, set()).add(zone)

        for source_backend, domains in sorted(backend_domains.items()):
            for replica_backend, replica_domains in sorted(
                backend_domains.items()
            ):
                if source_backend == replica_backend:
                    continue
                if not (domains & replica_domains):
                    continue
                for source_az in sorted(
                    backend_to_zones.get(source_backend, set())
                ):
                    for replica_az in sorted(
                        backend_to_zones.get(replica_backend, set())
                    ):
                        if source_az != replica_az:
                            return source_az, replica_az

        self.skipTest(
            'Could not find two distinct availability zones from different '
            'DHSS=True backends sharing the same replication_domain. '
            f'available_azs={sorted(available_azs)}, '
            f'backend_domains={backend_domains}, '
            f'backend_to_zones={backend_to_zones}'
        )

    def _cleanup_share_server_replicas(self, share_server_id):
        replicas = self.listing_result(
            'share server replica',
            f'list --share-server {share_server_id}',
            client=self.client,
        )

        non_active_ids = [
            item['ID']
            for item in replicas
            if item.get('Replica State', '').lower() != 'active'
        ]
        active_ids = [
            item['ID']
            for item in replicas
            if item.get('Replica State', '').lower() == 'active'
        ]

        for replica_id in non_active_ids:
            self.openstack(
                f'share server replica delete {replica_id} --force',
                client=self.client,
            )

        for replica_id in active_ids:
            self.openstack(
                f'share server replica delete {replica_id} --force',
                client=self.client,
            )

    def _create_share_server_replica(self, add_cleanup=True, properties=None):
        source_az, replica_az = self._get_two_availability_zones()

        share_type = self.create_share_type(
            data_utils.rand_name('test_share_server_replica_type'),
            dhss=True,
        )

        try:
            source_share_network = self.create_share_network(
                name='test_share_server_replica_source_network',
                availability_zone=source_az,
            )
            replica_share_network = self.create_share_network(
                name='test_share_server_replica_target_network',
                availability_zone=replica_az,
            )
        except tempest_exc.CommandFailed as error:
            self.skipTest(
                'Could not create availability-zone scoped share networks '
                f'for source AZ {source_az} and replica AZ {replica_az}: '
                f'{error}'
            )

        share = self.create_share(
            share_type=share_type['name'],
            share_network=source_share_network['id'],
            availability_zone=source_az,
            client=self.client,
        )

        share_instances = self.listing_result(
            'share instance',
            f'list --share {share["id"]}',
            client=self.client,
        )
        if not share_instances:
            self.skipTest('Share instance was not created for test share.')

        share_server_id = share_instances[0].get('Share Server ID')
        if not share_server_id:
            self.skipTest('Share server was not created for test share.')

        cmd = f'create {share_server_id}'
        cmd += f' --availability-zone {replica_az}'
        cmd += f' --share-network {replica_share_network["id"]}'
        if properties:
            for key, value in properties.items():
                cmd += f' --property {key}={value}'
        cmd += ' --wait'

        try:
            replica = self.dict_result(
                'share server replica',
                cmd,
                client=self.client,
            )
        except tempest_exc.CommandFailed as error:
            error_message = str(error)
            if (
                'No valid host was found' in error_message
                and 'share server replica scheduling' in error_message
            ):
                self.skipTest(
                    'No compatible host found for share server replica '
                    'scheduling in this environment.'
                )
            raise

        if add_cleanup:
            self.addCleanup(
                self._cleanup_share_server_replicas,
                share_server_id,
            )

        self.assertEqual(source_az, share.get('availability_zone'))
        self.assertEqual(replica_az, replica.get('availability_zone'))

        return replica, share_server_id

    def test_share_server_replica_create(self):
        """Test creating a share server replica."""
        replica, _share_server_id = self._create_share_server_replica()
        # Verify replica was created
        self.assertIsNotNone(replica['id'])
        self.assertIn('replica_state', replica)

    def test_share_server_replica_delete(self):
        """Test deleting a share server replica."""
        replica, share_server_id = self._create_share_server_replica(
            add_cleanup=False
        )
        replica_id = replica['id']

        # Delete the replica
        self.openstack(
            f'share server replica delete {replica_id} --force',
            client=self.client,
        )

        # Verify replica was deleted
        self.check_object_deleted('share server replica', replica_id)

        # Remove any remaining replica records tied to this share server.
        self._cleanup_share_server_replicas(share_server_id)

    def test_share_server_replica_create_with_metadata(self):
        """Create a replica with --property and verify it appears in show."""
        replica, _share_server_id = self._create_share_server_replica(
            properties={'custom_key': 'custom_value'}
        )
        # Verify replica was created with metadata
        self.assertIsNotNone(replica['id'])
        show_result = self.dict_result(
            'share server replica', f'show {replica["id"]}'
        )
        self.assertEqual(replica['id'], show_result['id'])
        metadata = str(show_result.get('metadata', ''))
        self.assertIn('custom_key', metadata)
        self.assertIn('custom_value', metadata)

    def test_share_server_replica_set_property(self):
        """Set a property on a replica and verify it appears in show."""
        replica, _share_server_id = self._create_share_server_replica()
        # Set a custom property
        self.openstack(
            f'share server replica set {replica["id"]}'
            ' --property test_key=test_value',
            client=self.client,
        )
        # Verify property was set
        show_result = self.dict_result(
            'share server replica', f'show {replica["id"]}'
        )
        metadata = str(show_result.get('metadata', ''))
        self.assertIn('test_key', metadata)
        self.assertIn('test_value', metadata)

    def test_share_server_replica_unset_property(self):
        """Unset a property from a replica and verify it is removed."""
        replica, _share_server_id = self._create_share_server_replica(
            properties={
                'custom_role': 'secondary',
                'custom_policy': 'async',
            }
        )
        # Unset the property
        self.openstack(
            f'share server replica unset {replica["id"]}'
            ' --property custom_role',
            client=self.client,
        )
        # Verify property was removed
        show_result = self.dict_result(
            'share server replica', f'show {replica["id"]}'
        )
        metadata = str(show_result.get('metadata', ''))
        self.assertNotIn('custom_role', metadata)
        self.assertIn('custom_policy', metadata)
        self.assertIn('async', metadata)

    def test_share_server_replica_list_with_share_server_filter(self):
        """List replicas filtered by share server and verify structure."""
        replica, share_server_id = self._create_share_server_replica()
        filtered_list = self.listing_result(
            'share server replica',
            f'list --share-server {share_server_id}',
        )
        self.assertTableStruct(
            filtered_list,
            [
                'ID',
                'Status',
                'Source Share Server ID',
                'Replica State',
                'Host',
                'Availability Zone',
            ],
        )
        self.assertIn(replica['id'], [item['ID'] for item in filtered_list])

    def test_share_server_replica_list(self):
        """Test listing share server replicas."""
        self._create_share_server_replica()
        # List all share server replicas
        replicas_list = self.listing_result('share server replica', 'list')
        # Verify table structure
        self.assertTableStruct(
            replicas_list,
            [
                'ID',
                'Status',
                'Source Share Server ID',
                'Replica State',
                'Host',
                'Availability Zone',
            ],
        )

    def test_share_server_replica_show(self):
        """Test showing a share server replica."""
        replica, _share_server_id = self._create_share_server_replica()
        show_result = self.dict_result(
            'share server replica', f'show {replica["id"]}'
        )
        self.assertEqual(replica['id'], show_result['id'])
        self.assertIn('availability_zone', show_result)
