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


from manilaclient import api_versions
from manilaclient import base
from manilaclient.common import constants

RESOURCES_PATH = '/share-server-replicas'
RESOURCE_PATH = '/share-server-replicas/%s'
RESOURCE_PATH_ACTION = '/share-server-replicas/%s/action'
RESOURCES_NAME = 'share_server_replicas'
RESOURCE_NAME = 'share_server_replica'


class ShareServerReplica(base.MetadataCapableResource):
    """A replica of a share server."""

    def __repr__(self):
        return f"<ShareServerReplica: {self.id}>"

    def promote(self):
        """Promote this share server replica to active."""
        self.manager.promote(self)

    def resync(self):
        """Re-sync this share server replica."""
        self.manager.resync(self)

    def reset_replica_state(self, replica_state):
        """Reset the 'replica_state' attr of the share server replica."""
        self.manager.reset_replica_state(self, replica_state)

    def reset_status(self, status):
        """Reset the 'status' attr of the share server replica."""
        self.manager.reset_status(self, status)


class ShareServerReplicaManager(base.MetadataCapableManager):
    """Manage :class:`ShareServerReplica` resources."""

    resource_class = ShareServerReplica
    resource_path = '/share-server-replicas'

    @api_versions.wraps(constants.SHARE_SERVER_REPLICA_VERSION)
    @api_versions.experimental_api
    def get(self, replica):
        """Get a share server replica.

        :param replica: either replica object or its UUID.
        :rtype: :class:`ShareServerReplica`
        """
        replica_id = base.getid(replica)
        return self._get(RESOURCE_PATH % replica_id, RESOURCE_NAME)

    @api_versions.wraps(constants.SHARE_SERVER_REPLICA_VERSION)
    @api_versions.experimental_api
    def list(self, share_server=None, search_opts=None):
        """List all share server replicas or replicas for a given server.

        :param share_server: either share server object or its UUID.
        :param search_opts: additional search options.
        :rtype: list of :class:`ShareServerReplica`
        """
        search_opts = search_opts or {}

        if share_server:
            search_opts['share_server_id'] = base.getid(share_server)

        query_string = self._build_query_string(search_opts)
        return self._list(
            RESOURCES_PATH + '/detail' + query_string, RESOURCES_NAME
        )

    @api_versions.wraps(constants.SHARE_SERVER_REPLICA_VERSION)
    @api_versions.experimental_api
    def create(
        self,
        share_server,
        availability_zone=None,
        share_network=None,
        metadata=None,
    ):
        """Create a share server replica.

        :param share_server: share server object or its UUID.
        :param availability_zone: optional availability zone name or UUID
            for the replica.
        :param share_network: optional share network object or its UUID.
        :param metadata: optional dict of custom key-value metadata.
        :rtype: :class:`ShareServerReplica`
        """
        body = {
            'share_server_id': base.getid(share_server),
        }

        if availability_zone:
            body['availability_zone'] = base.getid(availability_zone)

        if share_network is not None:
            body['share_network_id'] = base.getid(share_network)

        if metadata is not None:
            body['metadata'] = metadata

        return self._create(
            RESOURCES_PATH, {RESOURCE_NAME: body}, RESOURCE_NAME
        )

    @api_versions.wraps(constants.SHARE_SERVER_REPLICA_VERSION)
    @api_versions.experimental_api
    def delete(self, replica, force=False):
        """Delete a share server replica.

        :param replica: either replica object or its UUID.
        :param force: optional 'force' flag to forcefully delete.
        """
        replica_id = base.getid(replica)

        if force:
            self._action('force_delete', replica_id)
        else:
            self._delete(RESOURCE_PATH % replica_id)

    @api_versions.wraps(constants.SHARE_SERVER_REPLICA_VERSION)
    @api_versions.experimental_api
    def promote(self, replica):
        """Promote the provided share server replica to active.

        :param replica: either replica object or its UUID.
        """
        return self._action('promote', replica)

    @api_versions.wraps(constants.SHARE_SERVER_REPLICA_VERSION)
    @api_versions.experimental_api
    def resync(self, replica):
        """Re-sync the provided share server replica.

        :param replica: either replica object or its UUID.
        """
        return self._action('resync', replica)

    @api_versions.wraps(constants.SHARE_SERVER_REPLICA_VERSION)
    @api_versions.experimental_api
    def reset_replica_state(self, replica, replica_state):
        """Reset the 'replica_state' attr of the share server replica.

        :param replica: either replica object or its UUID.
        :param replica_state: state to set the replica's 'replica_state' to.
        """
        return self._action(
            'reset_replica_state', replica, {'replica_state': replica_state}
        )

    @api_versions.wraps(constants.SHARE_SERVER_REPLICA_VERSION)
    @api_versions.experimental_api
    def reset_status(self, replica, status):
        """Reset the 'status' attr of the share server replica.

        :param replica: either replica object or its UUID.
        :param status: state to set the replica's 'status' to.
        """
        return self._action('reset_status', replica, {'status': status})

    @api_versions.wraps(constants.SHARE_SERVER_REPLICA_VERSION)
    @api_versions.experimental_api
    def get_metadata(self, replica, subresource=None):
        """Get metadata of a share server replica.

        :param replica: either replica object or its UUID.
        :param subresource: optional child resource object or its UUID.
        """
        return super().get_metadata(replica, subresource=subresource)

    @api_versions.wraps(constants.SHARE_SERVER_REPLICA_VERSION)
    @api_versions.experimental_api
    def set_metadata(self, replica, metadata, subresource=None):
        """Set or update metadata for share server replica.

        :param replica: either replica object or its UUID.
        :param metadata: A dictionary of key:value pairs to be set as
            replica metadata
        :param subresource: optional child resource object or its UUID.
        """
        return super().set_metadata(replica, metadata, subresource=subresource)

    @api_versions.wraps(constants.SHARE_SERVER_REPLICA_VERSION)
    @api_versions.experimental_api
    def delete_metadata(self, replica, keys, subresource=None):
        """Delete specified keys from share server replica metadata.

        :param replica: either replica object or its UUID.
        :param keys: An iterable with keys of metadata items to be deleted
        :param subresource: optional child resource object or its UUID.
        """
        return super().delete_metadata(replica, keys, subresource=subresource)

    @api_versions.wraps(constants.SHARE_SERVER_REPLICA_VERSION)
    @api_versions.experimental_api
    def update_all_metadata(self, replica, metadata, subresource=None):
        """Update all metadata of a share server replica.

        :param replica: either replica object or its UUID.
        :param metadata: A dictionary of key:value pairs of replica metadata
            to be updated
        :param subresource: optional child resource object or its UUID.
        """
        return super().update_all_metadata(
            replica, metadata, subresource=subresource
        )

    def _action(self, action, replica, info=None, **kwargs):
        """Perform a share server replica 'action'.

        :param action: text with action name.
        :param replica: either replica object or its UUID.
        :param info: dict with data for specified 'action'.
        :param kwargs: dict with data to be provided for action hooks.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        replica_id = base.getid(replica)
        url = RESOURCE_PATH_ACTION % replica_id
        return self.api.client.post(url, body=body)
