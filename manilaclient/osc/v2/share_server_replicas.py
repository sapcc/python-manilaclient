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

import logging

from osc_lib.cli import parseractions
from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils as osc_utils

from manilaclient.common._i18n import _
from manilaclient.osc import utils


LOG = logging.getLogger(__name__)


class CreateShareServerReplica(command.ShowOne):
    """Create a share server replica."""

    _description = _("Create a replica of the given share server")

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "share_server",
            metavar="<share-server>",
            help=_("ID of the share server to replicate."),
        )
        parser.add_argument(
            "--property",
            metavar="<key=value>",
            default={},
            action=parseractions.KeyValueAction,
            help=_(
                "Set a property to this share server replica (repeat option "
                "to set multiple properties). "
            ),
        )
        parser.add_argument(
            "--wait",
            action="store_true",
            default=False,
            help=_("Wait for share server replica creation."),
        )
        parser.add_argument(
            "--availability-zone",
            metavar="<availability-zone>",
            default=None,
            help=_(
                "Availability zone in which the share server replica "
                "should be created."
            ),
        )
        parser.add_argument(
            '--share-network',
            metavar='<network-info>',
            default=None,
            help=_('Optional network info ID or name.'),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_server = osc_utils.find_resource(
            share_client.share_servers, parsed_args.share_server
        )

        kwargs = {
            "share_server": share_server,
        }

        if parsed_args.availability_zone:
            kwargs["availability_zone"] = parsed_args.availability_zone

        if parsed_args.share_network:
            share_network = osc_utils.find_resource(
                share_client.share_networks, parsed_args.share_network
            )
            kwargs['share_network'] = share_network.id

        if parsed_args.property:
            kwargs["metadata"] = utils.extract_key_value_options(
                parsed_args.property
            )

        replica = share_client.share_server_replicas.create(**kwargs)

        if parsed_args.wait:
            if not osc_utils.wait_for_status(
                status_f=share_client.share_server_replicas.get,
                res_id=replica.id,
                success_status=["inactive"],
            ):
                LOG.error(_("ERROR: Share server replica is in error state."))
            replica = osc_utils.find_resource(
                share_client.share_server_replicas, replica.id
            )

        replica._info.pop("links", None)
        return self.dict2columns(replica._info)


class DeleteShareServerReplica(command.Command):
    """Delete one or more share server replicas."""

    _description = _("Delete one or more share server replicas")

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "replica",
            metavar="<replica>",
            nargs="+",
            help=_("ID of the share server replica(s) to delete."),
        )
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help=_(
                "Attempt to force delete a share server replica on its "
                "backend. Using this option will purge the replica from "
                "Manila even if it is not cleaned up on the backend."
            ),
        )
        parser.add_argument(
            "--wait",
            action="store_true",
            default=False,
            help=_("Wait for share server replica deletion."),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        for replica in parsed_args.replica:
            try:
                share_client.share_server_replicas.delete(
                    replica, force=parsed_args.force
                )

                if parsed_args.wait:
                    if not osc_utils.wait_for_delete(
                        manager=share_client.share_server_replicas,
                        res_id=replica,
                    ):
                        result += 1

            except Exception as e:
                result += 1
                LOG.error(
                    _(
                        "Failed to delete a share server replica with "
                        "ID '%(replica)s': %(e)s"
                    ),
                    {"replica": replica, "e": e},
                )

        if result > 0:
            total = len(parsed_args.replica)
            msg = _(
                "%(result)s of %(total)s share server replicas "
                "failed to delete."
            ) % {
                "result": result,
                "total": total,
            }
            raise exceptions.CommandError(msg)


class ListShareServerReplica(command.Lister):
    """List share server replicas."""

    _description = _("List share server replicas")

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "--share-server",
            metavar="<share-server>",
            default=None,
            help=_(
                "ID of the share server to list share server replicas for."
            ),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_server = None
        if parsed_args.share_server:
            share_server = osc_utils.find_resource(
                share_client.share_servers, parsed_args.share_server
            )

        replicas = share_client.share_server_replicas.list(
            share_server=share_server
        )

        columns = [
            "id",
            "source_share_server_id",
            "status",
            "replica_state",
            "host",
            "availability_zone",
        ]

        column_headers = utils.format_column_headers(columns)
        data = (
            osc_utils.get_dict_properties(
                dict(
                    replica._info,
                    id=replica._info.get("id"),
                    source_share_server_id=(
                        ""
                        if replica._info.get("replica_state") == "active"
                        else replica._info.get("source_share_server_id")
                    ),
                ),
                columns,
            )
            for replica in replicas
        )

        return (column_headers, data)


class ShowShareServerReplica(command.ShowOne):
    """Show share server replica details."""

    _description = _("Show details about a share server replica")

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "replica",
            metavar="<replica>",
            help=_("ID of the share server replica."),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        replica = share_client.share_server_replicas.get(parsed_args.replica)
        replica._info.pop("links", None)
        return self.dict2columns(replica._info)


class SetShareServerReplica(command.Command):
    """Set share server replica properties."""

    _description = _(
        "Explicitly set the replica-state and/or status and/or property "
        "of a share server replica."
    )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "replica",
            metavar="<replica>",
            help=_("ID of the share server replica to modify."),
        )
        parser.add_argument(
            "--replica-state",
            "--replica_state",
            metavar="<replica-state>",
            choices=["in_sync", "out_of_sync", "active", "error"],
            help=_(
                "Assign a replica_state to the share server replica. "
                "Options include: in_sync, out_of_sync, active, error."
            ),
        )
        parser.add_argument(
            "--status",
            metavar="<status>",
            choices=[
                "active",
                "inactive",
                "error",
                "creating",
                "deleting",
                "error_deleting",
                "replication_change",
            ],
            help=_(
                "Assign a status to the share server replica. "
                "Options include: active, inactive, error, creating, "
                "deleting, error_deleting, replication_change."
            ),
        )
        parser.add_argument(
            "--property",
            metavar="<key=value>",
            default={},
            action=parseractions.KeyValueAction,
            help=_(
                "Set a property to this share server replica "
                "(repeat option to set multiple properties)."
            ),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        if (
            not parsed_args.replica_state
            and not parsed_args.status
            and not parsed_args.property
        ):
            raise exceptions.CommandError(
                _(
                    "Nothing to set. Please define "
                    "'--replica-state' or '--status' or '--property'."
                )
            )

        replica = osc_utils.find_resource(
            share_client.share_server_replicas, parsed_args.replica
        )

        if parsed_args.replica_state:
            try:
                share_client.share_server_replicas.reset_replica_state(
                    replica, parsed_args.replica_state
                )
            except Exception as e:
                result += 1
                LOG.error(
                    _(
                        "Failed to set replica_state "
                        "'%(replica_state)s': %(exception)s"
                    ),
                    {
                        "replica_state": parsed_args.replica_state,
                        "exception": e,
                    },
                )

        if parsed_args.status:
            try:
                share_client.share_server_replicas.reset_status(
                    replica, parsed_args.status
                )
            except Exception as e:
                result += 1
                LOG.error(
                    _("Failed to set status '%(status)s': %(exception)s"),
                    {
                        "status": parsed_args.status,
                        "exception": e,
                    },
                )

        if parsed_args.property:
            try:
                replica.set_metadata(parsed_args.property)
            except Exception as e:
                LOG.error(
                    _(
                        "Failed to set share server replica properties "
                        "'%(properties)s': %(exception)s"
                    ),
                    {"properties": parsed_args.property, "exception": e},
                )
                result += 1

        if result > 0:
            raise exceptions.CommandError(
                _("One or more of the set operations failed")
            )


class UnsetShareServerReplica(command.Command):
    """Unset a share server replica property."""

    _description = _("Unset a share server replica property")

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "--property",
            metavar="<key>",
            action="append",
            help=_(
                "Remove a property from share server replica "
                "(repeat option to remove multiple properties)."
            ),
        )
        parser.add_argument(
            "replica",
            metavar="<replica>",
            help=_("ID of the share server replica to unset property from."),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        replica = osc_utils.find_resource(
            share_client.share_server_replicas, parsed_args.replica
        )

        if parsed_args.property:
            result = 0
            for key in parsed_args.property:
                try:
                    replica.delete_metadata([key])
                except Exception as e:
                    result += 1
                    LOG.error(
                        _(
                            "Failed to unset share server replica property "
                            "'%(key)s': %(exception)s"
                        ),
                        {"key": key, "exception": e},
                    )
            if result > 0:
                raise exceptions.CommandError(
                    _("One or more of the unset operations failed")
                )
        else:
            raise exceptions.CommandError(
                "Please specify '--property <key>' to unset a property."
            )


class PromoteShareServerReplica(command.Command):
    """Promote a share server replica to active."""

    _description = _(
        "Promote the specified share server replica to 'active' replica_state."
    )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "replica",
            metavar="<replica>",
            help=_("ID of the share server replica to promote."),
        )
        parser.add_argument(
            "--wait",
            action="store_true",
            default=False,
            help=_("Wait for share server replica promotion."),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        replica = osc_utils.find_resource(
            share_client.share_server_replicas, parsed_args.replica
        )

        try:
            share_client.share_server_replicas.promote(replica)

            if parsed_args.wait:
                if not osc_utils.wait_for_status(
                    status_f=share_client.share_server_replicas.get,
                    res_id=replica.id,
                    success_status=["active"],
                    status_field="replica_state",
                ):
                    LOG.error(
                        _("ERROR: Share server replica is in error state.")
                    )

        except Exception as e:
            msg = "Failed to promote share server replica to 'active': %(e)s"
            raise exceptions.CommandError(msg % {"e": e})


class ResyncShareServerReplica(command.Command):
    """Resync a share server replica."""

    _description = _(
        "Attempt to update the share server replica with its 'active' mirror."
    )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "replica",
            metavar="<replica>",
            help=_("ID of the share server replica to resync."),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        replica = osc_utils.find_resource(
            share_client.share_server_replicas, parsed_args.replica
        )

        try:
            share_client.share_server_replicas.resync(replica)
        except Exception as e:
            msg = "Failed to resync share server replica: %(e)s"
            raise exceptions.CommandError(msg % {"e": e})
