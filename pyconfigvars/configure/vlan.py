from ..file import File
from ..network import Network, MACAddr


class Vlan:

    DEFAULT = {
        'VXLAN_BASE_ID': 10000,
        'VXLAN_PREFIX_NAME': 'vx',
        'BASE_CIDR': '10.0.0.0/8',
        'PREFIXLEN': 24,
    }

    RESERVED_L3VLAN = range(4000, 4091)

    def __init__(self, cidr=None, default_prefixlen=None):

        self.data = {}
        self._json_file = File('vlans')

        if cidr is None:
            cidr = self.DEFAULT['BASE_CIDR']
        if default_prefixlen is None:
            default_prefixlen = self.DEFAULT['PREFIXLEN']

        self._ipnetwork = Network(cidr, description='VLANs Base CIDR', is_parent=True)
        self._subnet = self._ipnetwork.iter_subnets(prefixlen=default_prefixlen)
        self._mac = MACAddr()
        self._macaddr = self._mac.iter_mac()

    @property
    def sorted_data(self):
        return {k: self.data[k] for k in sorted(self.data)}

    @property
    def _auto_cidrs(self):
        return {v['cidr']: k for k, v in self._json_file.items() if 'cidr' in v}

    # def base_cidr(self, cidr, default_prefixlen=None):
    #     prefixlen = (self.DEFAULT['AUTO_CIDR_PREFIXLEN']
    #                  if default_prefixlen is None else default_prefixlen)
    #
    #     self._ipnetwork = Network(cidr, description='VLANs Base CIDR', is_parent=True)
    #     self._subnet = self._ipnetwork.iter_subnets(prefixlen=prefixlen)
    #
    #     self._mac = MACAddr()
    #     self._macaddr = self._mac.iter_mac()

    def add(self, id, name, tenant, cidr=None, **kwargs):

        if id in self.data:
            raise AnsibleError('VLAN%s is already assign' % id)
        elif id in self.RESERVED_L3VLAN:
            raise AnsibleError('VLAN %s is reserved for L3VLAN' % id)

        if cidr is not None:
            self._set_network(id, name, cidr, tenant)
        else:
            cidr = self._get_network(id, name, tenant)

        network = Network(cidr)
        ip, prefix, host = network.last_ip()
        vmac = self._get_mac(id)

        self._set_data(
            id=id,
            name=name,
            cidr=cidr,
            tenant=tenant,
            vmac=vmac,
            vip=prefix,
            **kwargs,)

        self._tenant_vlans[tenant].add(id)

    def _set_network(self, id, name, cidr, tenant):

        if cidr in self._auto_cidrs:
            raise AnsibleError(
                'Network %s is already assign to VLAN%s' % (cidr, self._auto_cidrs[cidr]))

        try:
            self._remove_cidr(id)
        except KeyError:
            Network(cidr, description='VLAN%s:%s' % (id, name))
            self._set_json_file(id=id, tenant=tenant)

    def _get_mac(self, id):

        try:
            vmac = self._json_file[id]['vmac']
        except KeyError:
            vmac = next(self._macaddr)
            self._set_json_file(id=id, vmac=vmac)

        return vmac

    def _get_network(self, id, name, tenant):

        try:
            cidr = self._json_file[id]['cidr']
        except KeyError:
            cidr = next(self._subnet)
            Network(cidr, description='VLAN%s:%s' % (id, name))
            self._set_json_file(id=id, cidr=cidr, tenant=tenant)

        return cidr

    def _set_data(self, **kwargs):

        id = int(kwargs['id'])
        vxlan_id = self.DEFAULT['VXLAN_BASE_ID'] + id

        attrs = {
            'id': id,
            'name': kwargs.get('name'),
            'tenant': kwargs.get('tenant', 'default'),
            'cidr': kwargs.get('cidr'),
            'type': 'l3' if id > 3999 else 'l2',
            'nat': kwargs.get('nat'),
            'interface': {
                'vlan': {
                    'id': id,
                    'name': 'vlan%s' % id,
                    'virtual_ip': kwargs.get('vip'),
                    'virtual_mac': kwargs.get('vmac')
                },
                'vxlan': {
                    'id': vxlan_id,
                    'name': '%s%s' % (self.DEFAULT['VXLAN_PREFIX_NAME'], vxlan_id),
                }
            }
        }

        self.data[str(id)] = attrs

    def _set_json_file(self, **kwargs):

        id = int(kwargs['id'])

        try:
            attrs = self._json_file[str(id)]
            attrs.update(kwargs)
        except KeyError:
            self._json_file[str(id)] = kwargs

        if id > 3999:
            self._set_data(**kwargs)

    def _remove_cidr(self, id):
        try:
            self._ipnetwork.remove_subnet(self._json_file[id]['cidr'])
            del self._json_file[id]['cidr']
        except KeyError:
            pass

    def _remove_vmac(self, id):
        try:
            self._mac.remove(self._json_file[id]['vmac'])
            del self._json_file[id]['vmac']
        except KeyError:
            pass

    def _create_l3vlan(self):

        l3vlans = {v['tenant']: k for k, v in self._json_file.items() if int(k) > 3999}
        l3id = (r for r in range(4000, 4091) if str(r) not in l3vlans.values())

        for tenant in self._tenant_vlans:
            if tenant not in l3vlans:
                id = next(l3id)
                self._set_json_file(id=id, tenant=tenant)
                continue

            self._set_data(id=l3vlans[tenant], tenant=tenant)

    def save(self):

        self._create_l3vlan()

        for vid in list(self._json_file):
            if vid not in self.data:
                self._remove_cidr(vid)
                self._remove_vmac(vid)
                del self._json_file[vid]

        self._json_file.save()
        self._mac.save()
        self._ipnetwork.save()
