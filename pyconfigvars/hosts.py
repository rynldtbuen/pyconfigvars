from cumulus_custom_plugins.master import MasterConf
from cumulus_custom_plugins.helpers import print_warning


class HostsConf(MasterConf):

    def __init__(self):

        super().__init__()
        self.loopbacks()
        self.vlans()
        self.mlag()
        self.vxlans()
        self.svi()
        self.ip_interfaces()
        self.bgp_neighbors()
        self.server_interfaces()
        self.nat()

        hosts = [h for h in self.inventory['all']['hosts'] if h not in self.hosts]

        if len(hosts):
            print_warning(
                'INFO: %s does not have a configurations defined in master.yml' % ",".join(hosts))

    @property
    def config_mapping(self):
        return {
            'loopback': self.loopbacks,
            'mlag_bonds': self.mlag_bonds,
            'peerlink': self.peerlink,
            'bonds': self.bonds,
            'vxlan': self.vxlans,
            'svi': self.svi,
            'ip_interfaces': self.ip_ifaces,
            'unnumbered_interfaces': self.unnumbered_interfaces,
            'bgp': self.bgp_neighbors,
            'server_interfaces': self.server_interfaces,
            'nat': self.nat,
            'vrf_vni': self.vrf_vni,
            'interfaces': self.interfaces,
        }

    def get(self, config, host):
        try:
            return self.config_mapping[config][host]
        except KeyError:
            return None
