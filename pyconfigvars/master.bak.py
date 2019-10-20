import collections
import copy
import json
import os
import subprocess
import yaml
from itertools import groupby, permutations

from ansible.errors import AnsibleError
# from cumulus_custom_plugins.helpers import cluster, uncluster, get_id, NetworkLink, print_warning
# from cumulus_custom_plugins.ipnetwork import IPNetwork
# from cumulus_custom_plugins.file import File
import cumulus_custom_plugins.configure as configure


DEFAULT = {
    'VXLAN_PREFIX': 'vx',
    'BASE_VXLAN_ID': 100000,
    'VLAN_PREFIXLEN': 24,
    'BASE_VLAN_VIRTUAL_MAC': '44:38:39:FF:02:00',
    'MLAG': {
        'BASE_SYS_MAC': '44:38:39:FF:00:00',
        'BASE_ROUTER_MAC': '44:39:39:FF:01:00',
        'TOTAL_MAC': 256
    },
    'ROUTING_PROTOCOL': 'bgp',
    "MASTERFILE": 'master.yml'
}


def _defaultdict():
    return collections.defaultdict(_defaultdict)


class MasterConfig:

    filepath = "{}/{}".format(os.getcwd(), DEFAULT['MASTERFILE'])
    with open(filepath, 'r') as f:
        masterconfig = yaml.safe_load(f)

    command = 'ansible-inventory --list --inventory=devices'.split(' ')
    run = subprocess.run(command, stdout=subprocess.PIPE)
    ansible_inventory = json.loads(run.stdout)

    inventory = {}

    for group, v in ansible_inventory.items():
        if group != 'ungrouped' and 'hosts' in v:
            inventory[group] = [h for h in v['hosts']]

    configs = _defaultdict()

    def _add_interface(self, host, interface, **kwargs):
        if interface in self.configs['interfaces'][host]:
            raise AnsibleError('Interface %s is already assigned in %s' % (interface, host))
        self.configs['interfaces'][host][interface] = kwargs

    # def _loopbacks(self):
    #
    #     loopback = configure.loopback(
    #         cidr=self.masterconfig['loopback_base_cidr'],
    #         description='loopback'
    #     )
    #
    #     for _, hosts in self.inventory.items():
    #         for host in hosts:
    #             loopback.add(host, 'lo:0', alias='loopback0')
    #             for interface, attrs in loopback.json_data[host].items():
    #                 self._add_interface(host, interface, **attrs)
    #
    #     loopback.save()

    def _vlans(self):

        master_vlans = self.masterconfig['vlans']

        vlan = configure.vlan()
        vlan.base_cidr(master_vlans['base_cidr'], description='vlans base cidr')

        for tenant, vlans in master_vlans['tenants'].items():

            for _vlan in vlans:
                vlan.add(_vlan['id'], tenant=tenant, type='l2', **_vlan)

            vlan.get_l3vlan(tenant)


        self.configs['vlans'].update(vlan.data)
        vlan.save()
    #
    #         prefixlen = 23 if group == 'leaf' else 25
    #         subnet = IPnet(lo_cidr.get_subnet(prefixlen))
    #         subnet.existing_ips(list(loopback_ips[group].values()))
    #         ips = subnet.get_ips(type='lo')
    #
    #         for host in self.inventory[group]['hosts']:
    #             loopbacks[host] = next(ip)
    #             host_id = int(get_id(host)[1])
    #             loopbacks.setdefault(host, {})
    #             if host not in loopback_ips[group]:
    #                 loopback_ips[group][host] = next(ips)
    #
    #             loopbacks[host]['ip'] = loopback_ips[group][host]
    #
    #     return loopbacks
    #
    #     loopback_ips.dump()
    #
    #     self.loopbacks = loopbacks
        # self.base_cidrs()

    # def _build_attrs(self, attributes, **kwargs):
    #
    #     _attrs = {}
    #     for item in attributes:
    #         _attrs[item] = kwargs.get(item, None)
    #     return {k: v for k, v in sorted(_attrs.items(), key=lambda x: x[0])}
    #
    # def _add_interfaces(self, interfaces, host, assign_in, variable):
    #
    #     _interfaces = interfaces if isinstance(interfaces, list) else [interfaces]
    #
    #     for interface in _interfaces:
    #         if interface in self.interfaces[host]:
    #             t = tuple(v for k, v in self.interfaces[host][interface].items())
    #             zipped = zip(t, (assign_in, variable))
    #             _assign_in, _variable = [i if len(set(i)) > 1 else ",".join(set(i)) for i in zipped]
    #             raise AnsibleError(
    #                 "duplicate interface assignment: {}, {}, {} in {}".format(
    #                     interface, host, _assign_in, _variable))
    #
    #         self.interfaces[host][interface] = {
    #             'assign_in': assign_in, 'master_variable': variable}
    #
    # def _add_ip_interfaces(self, host, interface, attrs):
    #
    #     try:
    #         self._ip_interfaces[host][interface]
    #     except KeyError:
    #         self._ip_interfaces.setdefault(host, {})
    #
    #     self._ip_interfaces[host][interface] = attrs
    #
    # def base_cidrs(self):
    #
    #     base_cidrs = self.masterconf['BASE_CIDRS']
    #     _overlapping_cidrs = overlapping_cidrs(list(base_cidrs.values()))
    #
    #     if _overlapping_cidrs:
    #         raise AnsibleError(
    #             "overlapping CIDRS: {} in BASE_CIDRS".format(_overlapping_cidrs))
    #     for k, v in base_cidrs.items():
    #         self.cidrs[v] = {'master_variable': 'BASE_CIDRS', 'assign_to': k}
    #
    #     self.base_cidrs = base_cidrs
#
#         self.vlans = {_k: _v for _, v in vlans.items() for _k, _v in v.items()}
#         self._vlan_cidr()
#         self._vlan_interface()
#         self._vxlan_interface()
#
    @property
    def _vlan_prefix(self):
        pass
#
#         vlans_cidr = FileConf('vlans_cidrs')
#         for _vid in list(vlans_cidr):
#             if _vid not in self.vlans:
#                 del vlans_cidr[_vid]
#
#         base_cidrs = self.base_cidrs['vlan']
#         vlan_base_cidr = IPnet(base_cidrs)
#         vlan_base_cidr.existing_subnets([v['cidr'] for _, v in vlans_cidr.items()])
#         vlans = [v for k, v in self.vlans.items() if v['type'] == 'l2']
#         auto_subnets = vlan_base_cidr.get_subnets(DEFAULT_VLAN_PREFIXLEN)
#
#         for vlan in vlans:
#             if vlan['cidr'] is None:
#                 if vlan['vid'] not in vlans_cidr or vlan['vid'] in vlans_cidr and (
#                         vlans_cidr[vlan['vid']]['allocation'] != 'auto_cidr'):
#                     cidr = next(auto_subnets)
#                     vlan['cidr'] = cidr
#                     vlan['prefixlen'] = DEFAULT_VLAN_PREFIXLEN
#                     vlans_cidr[vlan['vid']] = {'cidr': cidr, 'allocation': 'auto_cidr'}
#                 else:
#                     vlan['cidr'] = vlans_cidr[vlan['vid']]['cidr']
#                     vlan['prefixlen'] = DEFAULT_VLAN_PREFIXLEN
#
#             elif vlan['prefixlen'] is not None:
#                 if vlan['vid'] not in vlans_cidr or vlan['vid'] in vlans_cidr and (
#                         vlans_cidr[vlan['vid']]['allocation'] != 'auto_prefixlen'):
#                     cidr = vlan_base_cidr.get_subnet(vlan['prefixlen'])
#                     vlan['cidr'] = cidr
#                     vlans_cidr[vlan['vid']] = {'cidr': cidr, 'allocation': 'auto_prefixlen'}
#                 else:
#                     vlan['cidr'] = vlans_cidr[vlan['vid']]['cidr']
#
#             else:
#                 cidr = IPnet(vlan['cidr'])
#                 if cidr.overlaps_with(list(self.cidrs)):
#                     raise AnsibleError(
#                         "overlapping cidrs: {}, check the VLANS and BASE_CIDRS "
#                         "variable in master.yml".format(
#                             cidr.overlaps_with(list(self.cidrs))))
#                 elif vlan['vid'] in vlans_cidr:
#                     del vlans_cidr[vlan['vid']]
#                 vlan['prefixlen'] = cidr.prefixlen
#
#         _overlapping_cidrs = overlapping_cidrs([i['cidr'] for i in vlans if i['cidr']])
#         if _overlapping_cidrs:
#             raise AnsibleError(
#                 "overlapping cidrs: {} in VLANS".format(_overlapping_cidrs))
#
#         vlans_cidr.dump()
#
#     def _vlan_interface(self):
#
#         vlans = [v for _, v in self.vlans.items()]
#
#         for vlan in vlans:
#             if vlan['type'] == 'l3':
#                 vlan['vlan'] = {'name': 'vlan' + vlan['vid'], 'vid': vlan['vid']}
#                 continue
#
#             cidr = IPnet(vlan['cidr'])
#             vlan['vlan'] = {
#                 'name': 'vlan' + vlan['vid'],
#                 'virtual_ip': cidr.get_ip(-1),
#                 'vid': vlan['vid'],
#                 'virtual_hwaddr': MACAddr(
#                     DEFAULT_VLAN_BASE_VIRTUAL_MAC) + int(vlan['vid'])}
#             # else:
#             #     vlan['vlan'] = {'name': 'vlan' + vlan['vid'], 'vid': vlan['vid']}
#
#         # server_gateways = FileConf('server_gateways')
#         # allowed_nat_vlans = collections.defaultdict(list)
#         #
#         # gateways = []
#         # for _, v in self.vlans.items():
#         #     if v['allow_nat']:
#         #         allowed_nat_vlans[v['tenant']].append(v['vlan'])
#         #         gw = v['vlan']['virtual_ip'].split(',')[0]
#         #
#         # server_gateways.new_keys(gateways)
#         #
#         # for tenant, vlans in allowed_nat_vlans.items():
#         #     metric = (r for r in range(1, 11) if r not in [v for k, v in server_gateways.items()])
#         #     for vlan in vlans:
#         #         gw = vlan['virtual_ip'].split('/')[0]
#         #         if gw not in server_gateways:
#         #             server_gateways[gw] = next(metric)
#         #
#         #         self.vlans[vlan['vid']]['vlan']['metric'] = server_gateways[gw]
#
#         # self.server_gateways = server_gateways
#
#     def _vxlan_interface(self):
#
#         vlans = [v for _, v in self.vlans.items()]
#
#         for vlan in vlans:
#             id = str(DEFAULT_VXLAN_BASE_ID + int(vlan['vid']))
#             name = DEFAULT_VXLAN_PREFIX + id
#             vlan['vxlan'] = {'id': id, 'name': name}
#
#     def mlag_bonds(self):
#
#         def _add_clag_interface(bonds, rack):
#
#             existing_clag_ids = [v for k, v in mlag_config[rack]['clag_interfaces'].items()]
#
#             clag_ids = (r for r in range(1, 200) if r not in existing_clag_ids)
#
#             for bond in bonds:
#                 if bond not in mlag_config[rack]['clag_interfaces']:
#                     mlag_config[rack]['clag_interfaces'][bond] = next(clag_ids)
#
#                 mlag['bonds'][bond]['clag_id'] = mlag_config[rack]['clag_interfaces'][bond]
#
#         def _tenant(vids, bond, rack):
#             tenant = set()
#             for vid in uncluster(vids):
#                 if vid not in vlans:
#                     raise AnsibleError(
#                         "vid does not exist in VLANS: {}, {}, {} in MLAG"
#                         "".format(vid, bond, rack))
#                 tenant.add(vlans[vid]['tenant'])
#             if len(tenant) > 1:
#                 raise AnsibleError(
#                     "vids belongs to multiple tenant: {}, {}, {} in MLAG"
#                     "".format(vids, bond, rack))
#
#             return "".join(tenant)
#
#         mlag_config = FileConf('mlag_config')
#         clag_cidr = IPnet(self.base_cidrs['clag_vxlan_anycast'])
#         clag_cidr.existing_ips([v['anycast_ip'] for _k, v in mlag_config.items()])
#         get_anycast_ip = clag_cidr.get_ips(type='addr')
#         vlans = self.vlans
#         # clag_interfaces = FileConf('clag_interfaces')
#
#         base_sys_mac = DEFAULT['MLAG']['BASE_SYS_MAC']
#         base_router_mac = DEFAULT['MLAG']['BASE_ROUTER_MAC']
#         total = DEFAULT['MLAG']['TOTAL_MAC']
#
#         sys_mac = MACAddr(base_sys_mac, total)
#         get_sys_mac = sys_mac.get_uniq_mac([v['sys_mac'] for _, v in mlag_config.items()])
#
#         router_mac = MACAddr(base_router_mac, total)
#         get_router_mac = router_mac.get_uniq_mac([v['router_mac'] for _, v in mlag_config.items()])
#
#         mlag_bonds = {}
#         mlag_hosts = {}
#         rack_exist = []
#
#         for rack, v in self.masterconf['MLAG'].items():
#
#             exist = True
#
#             for host in v['hosts'].split(','):
#                 if host not in mlag_hosts:
#                     mlag_hosts[host] = rack
#                 else:
#                     raise AnsibleError(
#                         'Duplicate assignment of MLAG host: %s assigned in (%s,%s)'
#                         % (host, rack, mlag_hosts[host]))
#
#                 if host not in self.inventory['all']['hosts']:
#                     print_warning('INFO: %s is not defined in inventory(devices)' % host)
#                     exist = False
#                     continue
#
#                 self.hosts.add(host)
#
#             if exist:
#                 rack_exist.append(rack)
#
#                 if rack not in mlag_config:
#                     mlag_config[rack] = {
#                         'sys_mac': next(get_sys_mac),
#                         'router_mac': next(get_router_mac),
#                         'anycast_ip': next(get_anycast_ip),
#                         'clag_interfaces': {}
#                     }
#
#                 _sys_mac = mlag_config[rack]['sys_mac']
#                 _router_mac = mlag_config[rack]['router_mac']
#                 _anycast_ip = mlag_config[rack]['anycast_ip']
#
#                 # mlag = {'bonds': {}, 'bridge': {}, 'peerlink': {}, 'summary': {}}
#                 mlag = {'bonds': {}, 'peerlink': {}, 'summary': {}}
#
#                 for bond in v['bonds']:
#                     if bond['name'] in mlag['bonds']:
#                         raise AnsibleError(
#                             "duplicate bond: {}, {} in MLAG".format(bond['name'], rack))
#                     slaves, vids = uncluster(bond['slaves']), uncluster(bond['vids'])
#                     self._add_interfaces(slaves, rack, bond['name'], 'MLAG')
#                     bond['vids'] = cluster(vids)
#                     bond['slaves'] = ",".join(slaves)
#                     mlag['bonds'].setdefault(bond['name'], {}).update(
#                         self._build_attrs(
#                             ATTRIBUTES['BOND'],
#                             tenant=_tenant(bond['vids'], bond['name'], rack),
#                             mode='access' if len(vids) < 2 else 'trunk',
#                             rack=rack, **bond)
#                     )
#
#                 _add_clag_interface(mlag['bonds'].keys(), rack)
#
#                 peerlink_interfaces = uncluster(v['peerlink_interfaces'])
#                 self._add_interfaces(
#                     peerlink_interfaces, rack, 'peerlink', 'MLAG')
#                 mlag['peerlink'] = {
#                     'interfaces': ",".join(peerlink_interfaces),
#                     'sys_mac': _sys_mac}
#
#                 slaves, vids, tenants = set(), set(), set()
#                 for _, _v in mlag['bonds'].items():
#                     slaves.update(uncluster(_v['slaves']))
#                     vids.update(uncluster(_v['vids']))
#                     tenants.add(_v['tenant'])
#
#                 slaves.update(uncluster(mlag['peerlink']['interfaces']))
#                 vids.update([k for k, v in vlans.items()
#                             if v['type'] == 'l3' and v['tenant'] in tenants])
#
#                 mlag['summary'] = {
#                     'bonds': cluster(list(mlag['bonds'])), 'slaves': cluster(slaves),
#                     'vids': cluster(vids), 'tenants': cluster(tenants),
#                     'router_hwaddr': _router_mac,
#                     'clag_anycast_ip': _anycast_ip,
#                     'hosts': v['hosts']
#                 }
#                 # bridge = []
#                 # for k, v in groupby(list(mlag['bonds'].values()), lambda x: x['vids']):
#                 #     bridge.append({
#                 #         'bonds': cluster([i['name'] for i in v], start_name=False),
#                 #         'mode': 'access' if len(uncluster(k)) < 2 else 'vids',
#                 #         'vids': k})
#                 # mlag['bridge'] = bridge
#
#                 mlag_bonds[rack] = mlag
#
#         mlag_config.new_keys(rack_exist)
#
#         for rack in rack_exist:
#             for bond in list(mlag_config[rack]['clag_interfaces']):
#                 if bond not in mlag_bonds[rack]['bonds']:
#                     del mlag_config[rack]['clag_interfaces'][bond]
#
#         mlag_config.dump()
#
#         self.mlag_bonds = mlag_bonds
#
#     def mlag(self):
#
#         self.mlag_bonds()
#         mlag = {}
#
#         for rack, v in self.mlag_bonds.items():
#             hosts = v['summary']['hosts'].split(',')
#             for idx, host in enumerate(hosts):
#                 peer = hosts[idx - 1]
#                 backup_ip = self.loopbacks[peer]['ip'].split('/')[0]
#                 host_id = int(get_id(host)[1])
#                 if idx == 0:
#                     clag_role = '2000'
#                     ip, peer_ip = '169.254.1.2/30', '169.254.1.1'
#                 else:
#                     clag_role = '1000'
#                     ip, peer_ip = '169.254.1.1/30', '169.254.1.2'
#
#                 self.loopbacks[host]['clag_anycast_ip'] = v['summary']['clag_anycast_ip']
#
#                 mlag.setdefault(host, {})
#                 # mlag[host].update({
#                 #    'bonds': v['bonds'], 'bridge': v['bridge'], 'summary': v['summary']})
#                 mlag[host].update({
#                     'bonds': v['bonds'], 'summary': v['summary']})
#                 mlag[host]['peerlink'] = {
#                     'role': clag_role, 'ip': ip, 'peer_ip': peer_ip,
#                     'backup_ip': backup_ip, 'peer': peer}
#                 mlag[host]['peerlink'].update(v['peerlink'])
#
#                 for interface, _v in self.interfaces[rack].items():
#                     self._add_interfaces(
#                         interface, host, _v['assign_in'], _v['master_variable'])
#
#         self._mlag = mlag
#
#         self.peerlink = {k: v['peerlink'] for k, v in self._mlag.items()}
#         self.bonds = {k: v['bonds'] for k, v in self._mlag.items()}
#
#     def vxlans(self):
#
#         vrf_vni = {}
#         vxlans = {}
#
#         for host, v in self._mlag.items():
#
#             vlans = [self.vlans[vid] for vid in uncluster(v['summary']['vids'])]
#             interfaces = {}
#             vrf_vni[host] = {}
#
#             for vlan in vlans:
#                 interface = vlan['vxlan']
#                 attrs = {**vlan, **interface}
#                 interfaces[interface['name']] = self._build_attrs(
#                     ATTRIBUTES['VXLAN'], **attrs)
#
#                 if vlan['type'] == 'l3':
#                     vrf_vni[host][vlan['tenant']] = interface['id']
#
#             vxlans[host] = {
#                 'interfaces': interfaces,
#                 # 'vni': cluster(list(interfaces), start_name=False),
#                 'local_tunnelip': self.loopbacks[host]['ip'].split('/')[0]}
#
#         # Add all l3vni in border leaf
#         _vrf_vni = {
#             v['tenant']: v['vxlan']['id']
#             for k, v in self.vlans.items() if v['type'] == 'l3'}
#
#         l3vlans = [v for _, v in self.vlans.items() if v['type'] == 'l3']
#
#         for host in self.inventory['border']['hosts']:
#             interfaces = {}
#             for vlan in l3vlans:
#                 interface = vlan['vxlan']
#                 attrs = {**vlan, **interface}
#                 interfaces[interface['name']] = self._build_attrs(
#                     ATTRIBUTES['VXLAN'], **attrs)
#
#             vxlans[host] = {
#                 'interfaces': interfaces,
#                 'vni': cluster(list(interfaces), start_name=False),
#                 'local_tunnelip': self.loopbacks[host]['ip'].split('/')[0]}
#
#             vrf_vni[host] = _vrf_vni
#
#         self.vrf_vni = vrf_vni
#         self.vxlans = vxlans
#
#     def svi(self):
#
#         svi = {}
#
#         for host, v in self._mlag.items():
#             host_id = int(get_id(host)[1])
#             vlans = [self.vlans[vid] for vid in uncluster(v['summary']['vids'])]
#             interfaces = {}
#             for vlan in vlans:
#                 interface = vlan['vlan']
#                 attrs = {**vlan, **interface}
#                 try:
#                     cidr = IPnet(vlan['cidr'])
#                     ip = cidr.get_ip(-(host_id + 1))
#                     interfaces[interface['vid']] = self._build_attrs(
#                         ATTRIBUTES['SVI'], ip=ip, **attrs)
#                 except TypeError:
#                     router_hwaddr = v['summary']['router_hwaddr']
#                     interfaces[interface['vid']] = self._build_attrs(
#                         ATTRIBUTES['SVI'], router_hwaddr=router_hwaddr, **attrs)
#
#             svi[host] = interfaces
#
#         for host in self.inventory['border']['hosts']:
#             l3vlans = [v for _, v in self.vlans.items() if v['type'] == 'l3']
#
#             interfaces = {}
#
#             for vlan in l3vlans:
#                 interfaces[vlan['vlan']['vid']] = self._build_attrs(
#                     ATTRIBUTES['SVI'], **vlan)
#
#             svi[host] = interfaces
#
#         self.svi = svi
#
#     def _bgp_config(self):
#
#         master = self.masterconf['BASE_BGP_AS']
#         seen = set()
#         bgp_config = {}
#
#         for group, asn in master.items():
#             if asn in seen:
#                 raise AnsibleError(
#                     "duplicate base bgp as: {} in BASE_BGP_AS".format(asn))
#
#             seen.add(asn)
#
#             for host in self.inventory[group]['hosts']:
#                 bgp_config.setdefault(host, {})
#                 host_id = int(get_id(host)[1])
#                 _as = asn if group == 'spine' else asn + (host_id - 1)
#                 bgp_config[host]['as'] = str(_as)
#                 bgp_config[host]['router_id'] = self.loopbacks[host]['ip'].split('/')[0]
#
#         self.bgp_config = bgp_config
#
#     def _peer_group(self, host):
#
#         groups = []
#
#         for group, v in self.inventory.items():
#             try:
#                 if host in v['hosts']:
#                     groups.append(group)
#             except KeyError:
#                 pass
#
#         return groups
#
#     def bgp_neighbors(self):
#
#         self._bgp_config()
#
#         # host_not_defined = set()
#         bgp_neighbors = {}
#
#         for host, interfaces in self.bgp_interfaces.items():
#             neighbors, peer_groups, = {}, set()
#             for interface, v in interfaces.items():
#                 # try:
#                 vrf = 'default' if not v['vrf'] else v['vrf']
#                 rhost, rinterface = v['remote_host'], v['remote_interface']
#
#                 if rhost in self.inventory['all']['hosts']:
#
#                     if not v['address']:
#                         neighbor = interface
#                     elif v['address'] and v['remote_vif']:
#                         neighbor = self.bgp_interfaces[rhost][v['remote_vif']]['address']
#                     else:
#                         neighbor = self.bgp_interfaces[rhost][rinterface]['address']
#
#                     remote_as = 'external' if not v['address'] else self.bgp_config[rhost]['as']
#                     remote_id = self.bgp_config[rhost]['router_id']
#                     peer_group = self._peer_group(rhost)
#                     peer_groups.update(peer_group)
#                     neighbors.setdefault(vrf, []).append({
#                         'neighbor': neighbor.split('/')[0], 'remote_as': remote_as,
#                         'remote_id': remote_id, 'peer_group': peer_group,
#                         'remote_host': rhost})
#                 # except KeyError:
#                 #     pass
#
#             # try:
#             bgp_neighbors[host] = {
#                 'neighbors': neighbors,
#                 'peer_groups': [g for g in peer_groups if g in self.MAIN_GROUPS]}
#             bgp_neighbors[host].update(self.bgp_config[host])
#             # except KeyError as er:
#             #     print_warning("%s is not defined in inventory" % er)
#
#         self.bgp_neighbors = bgp_neighbors
#
#     def server_interfaces(self):
#
#         vlans = self.vlans
#         oob_mgmt_gw = self.masterconf['OOB_MGMT']['gateway_address']
#         server_gateways = FileConf('server_gateways')
#         server_interfaces = {}
#         gateways = collections.defaultdict(list)
#
#         for host, interface in self.masterconf['SERVER_INTERFACES'].items():
#
#             if host not in self.inventory['all']['hosts']:
#                 print_warning('INFO: %s is not defined in inventory(devices)' % host)
#                 continue
#
#             # host_id = int(get_id(host)[1])
#             # _interfaces = {
#             #     'mgmt': {},
#             #     'interfaces': [],
#             #     'bonds': {},
#             #     'bridge': {},
#             #     'vlans_interface': {}
#             # }
#             #
#             # for bond in interface['bonds']:
#             #     rack = bond['uplink']
#             #     if rack not in self.mlag_bonds:
#             #         raise AnsibleError(
#             #             'Bond uplink does not exist: %s' % rack
#             #         )
#         #         mlag_bonds = self.mlag_bonds[rack]['bonds']
#         #         for bond in bonds:
#         #             if bond['name'] not in mlag_bonds:
#         #                 raise AnsibleError(
#         #                     "bond does not exist in MLAG['{}']': {}, {} in "
#         #                     "SERVER_INTERFACES".format(rack, bond['name'], host))
#         #
#         #             elif bond['name'] in _interfaces['bonds']:
#         #                 raise AnsibleError(
#         #                     "duplicate bond': {}, {} in "
#         #                     "SERVER_INTERFACES".format(bond['name'], host))
#         #
#         #             _interfaces['bonds'][bond['name']] = self._build_attrs(
#         #                 ATTRIBUTES['BOND'], name=bond['name'],
#         #                 slaves=" ".join(uncluster(bond['slaves'])),
#         #                 tenant=mlag_bonds[bond['name']]['tenant'],
#         #                 vids=mlag_bonds[bond['name']]['vids'],
#         #                 rack=rack)
#         #
#         #             _interfaces['mgmt'] = {
#         #                 'port': interface['mgmt_port'],
#         #                 'gateway': oob_mgmt_gw
#         #             }
#         #
#         #             slaves = uncluster(bond['slaves'])
#         #
#         #             self._add_interfaces(slaves, host, bond['name'], 'SERVER_INTERFACES')
#         #
#         #             _interfaces['interfaces'].extend(slaves)
#         #
#         #     self._add_interfaces(interface['mgmt_port'], host, 'mgmt_port', 'SERVER_INTERFACES')
#         #
#         #     vids, ports = set(), set()
#         #     for bond in _interfaces['bonds'].values():
#         #         vids.update(uncluster(bond['vids']))
#         #         ports.add(bond['name'])
#         #
#         #     _interfaces['bridge'] = {
#         #         'vids': " ".join(cluster(vids).split(',')),
#         #         'ports': " ".join(sorted(ports))
#         #     }
#         #
#         #     try:
#         #         metric = (r for r in range(1, 11)
#         #                   if r not in [v for k, v in server_gateways[host].items()])
#         #     except KeyError:
#         #         metric = (r for r in range(1, 11))
#         #
#         #     if host not in server_gateways:
#         #         server_gateways[host] = {}
#         #
#         #     for vid in vids:
#         #
#         #         _gateway = None
#         #         _metric = None
#         #         interface = vlans[vid]['vlan']
#         #
#         #         if vlans[vid]['allow_nat']:
#         #             _gateway = interface['virtual_ip'].split('/')[0]
#         #             if _gateway not in server_gateways[host]:
#         #                 server_gateways[host][_gateway] = next(metric)
#         #             _metric = server_gateways[host][_gateway]
#         #             gateways[host].append(_gateway)
#         #
#         #         ip = IPnet(vlans[vid]['cidr']).get_ip(host_id)
#         #
#         #         _interfaces['vlans_interface'][interface['name']] = {
#         #             'alias': vlans[vid]['name'], 'ip': ip, 'gateway': _gateway,
#         #             'vid': vid, 'raw_device': 'bridge', 'metric': _metric}
#         #
#         #     server_interfaces[host] = _interfaces
#         #
#         #     self.hosts.add(host)
#         #
#         # self.server_interfaces = server_interfaces
#
#         # for host, gws in server_gateways.copy().items():
#         #     if host in master:
#         #         for gw, _ in gws.copy().items():
#         #             if gw not in gateways[host]:
#         #                 del server_gateways[host][gw]
#         #         continue
#         #
#         #     del server_gateways[host]
#         #
#         # server_gateways.dump()
#
#     def _unnumbered_interfaces(self):
#
#         master = {
#             k: v for k, v in self.masterconf['TOPOLOGY'].items()
#             if v['type'] == 'unnumbered'}
#
#         for k, v in master.items():
#             protocol = v.get('protocol', DEFAULT_PROTOCOL)
#             links = NetworkLink(k, v['links'], v['type'], protocol=protocol)
#             for item in links.data:
#                 self._add_interfaces(
#                     item['interface'], item['host'], item['network'], 'TOPOLOGY')
#
#                 self._add_ip_interfaces(
#                     item['host'], item['interface'],
#                     self._build_attrs(ATTRIBUTES['IP_INTERFACE'], **item))
#
#     def _ip_interfaces_master(self):
#
#         master = self.masterconf['IP_INTERFACES']
#
#         for host, interfaces in master.items():
#
#             self._add_interfaces(
#                 [i['name'] for i in interfaces], host, 'ip_interfaces', 'IP_INTERFACES')
#             for interface in interfaces:
#                 self._add_ip_interfaces(
#                     host, interface['name'],
#                     self._build_attrs(ATTRIBUTES['IP_INTERFACE'], **interface))
#
#     def _sub_interfaces(self):
#
#         l3vlans = {k: v['tenant'] for k, v in self.vlans.items() if v['type'] == 'l3'}
#         ipnetwork_links = FileConf('ipnetwork_links')
#         master = {
#             k: v for k, v in self.masterconf['TOPOLOGY'].items()
#             if v['type'] == 'sub_interface'}
#
#         data, link_ids = [], []
#
#         for network, v in master.items():
#             if network not in self.base_cidrs:
#                 raise AnsibleError(
#                     "network cidr not found: %s, define it in BASE_CIDRS" % network)
#
#             nl = NetworkLink(network, v['links'], v['type'], protocol=DEFAULT_PROTOCOL)
#             _link_ids = sorted(
#                 ["{}_{}".format(link, vif)
#                  for link in nl.link_ids()
#                  for vif in l3vlans], key=lambda x: x[1])
#
#             ipnetwork_links.new_keys(_link_ids)
#             base_cidr = IPnet(self.base_cidrs[network])
#
#             try:
#                 base_cidr.existing_subnets(list(ipnetwork_links.values()))
#             except TypeError:
#                 pass
#
#             subnets = base_cidr.get_subnets(30)
#
#             for link_id in _link_ids:
#                 if link_id not in ipnetwork_links:
#                     ipnetwork_links[link_id] = next(subnets)
#                 link_ids.append(link_id)
#
#             for item in nl.data:
#                 self._add_interfaces(
#                     item['interface'], item['host'], item['network'], 'TOPOLOGY')
#
#             data.extend(nl.data)
#
#         for link_id, subnet in ipnetwork_links.items():
#
#             ips = IPnet(subnet).get_ips()
#             link, vif = link_id.split('_')
#
#             for item in data:
#
#                 item['vrf'] = l3vlans[vif]
#                 remote_vif = "{}.{}".format(item['remote_interface'], vif)
#                 interface = "{}.{}".format(item['interface'], vif)
#
#                 if item['link_id'] == link:
#                     address = next(ips)
#                     self._add_interfaces(
#                         interface, item['host'], item['network'], 'TOPOLOGY')
#
#                     self._add_ip_interfaces(
#                         item['host'], interface, self._build_attrs(
#                             ATTRIBUTES['IP_INTERFACE'], remote_vif=remote_vif,
#                             address=address, **item))
#         #     else:
#         #         del ipnetwork_links[link_id]
#         #
#         ipnetwork_links.dump()
#
#     def ip_interfaces(self):
#
#         self._unnumbered_interfaces()
#         self._ip_interfaces_master()
#         self._sub_interfaces()
#
#         def _add_interface(host, interface, value, variable):
#             try:
#                 variable[host][interface] = value
#             except KeyError:
#                 variable.setdefault(host, {})
#                 variable[host][interface] = value
#
#         bgp, nat, ip, un = {}, {}, {}, {}
#
#         for host, interfaces in self._ip_interfaces.items():
#
#             if host not in self.inventory['all']['hosts']:
#                 print_warning('INFO: %s is not defined in inventory(devices)' % host)
#                 continue
#
#             for interface, v in interfaces.items():
#                 if v['protocol'] == 'bgp':
#                     _add_interface(host, interface, v, bgp)
#                 if v['nat']:
#                     _add_interface(host, interface, v, nat)
#                 if v['address']:
#                     _add_interface(host, interface, v, ip)
#                 else:
#                     _add_interface(host, interface, v, un)
#
#             self.hosts.add(host)
#
#         self.bgp_interfaces = bgp
#         self.nat_interfaces = nat
#         self.ip_ifaces = ip
#         self.unnumbered_interfaces = un
#
#     def nat(self):
#
#         oob_mgmt_cidr = self.base_cidrs['oob_management']
#         nat = FileConf('nat')
#         ids = (r for r in range(500, 1000, 10)
#                if r not in [v['base_rule'] for _, v in nat['sources'].items()])
#         allow_nat_vlans = {v['cidr']: v for k, v in self.vlans.items() if v['allow_nat']}
#
#         if len(nat) == 0:
#             nat.update({'sources': {}, 'hosts': {}})
#
#         if oob_mgmt_cidr not in nat['sources']:
#             nat['sources'][oob_mgmt_cidr] = {
#                 'base_rule': 0, 'description': 'default:oob_management'
#             }
#
#         nat_sources = []
#
#         for source, v in allow_nat_vlans.items():
#             if source not in nat['sources']:
#                 base_rule = next(ids)
#                 nat['sources'][source] = {
#                     'description': '%s:%s' % (v['name'], v['tenant']), 'base_rule': base_rule
#                 }
#             else:
#                 nat['sources'][source]['description'] = '%s:%s' % (v['name'], v['tenant'])
#
#             nat_sources.append(source)
#
#         _sources = []
#
#         for source in list(nat['sources']):
#             if source != oob_mgmt_cidr and source not in nat_sources:
#                 del nat['sources'][source]
#                 _sources.append(source)
#
#         for host, sources in nat['hosts'].copy().items():
#             if host not in self.nat_interfaces:
#                 del nat['hosts'][host]
#                 continue
#
#             for source, items in sources.copy().items():
#                 if source in _sources:
#                     del nat['hosts'][host][source]
#                     continue
#
#                 for idx, item in enumerate(items):
#                     if item['interface'] not in self.nat_interfaces[host]:
#                         nat['hosts'][host][source].pop(idx)
#
#         for host, interfaces in self.nat_interfaces.items():
#
#             if host not in nat['hosts']:
#                 nat['hosts'][host] = {}
#
#             nat_host = nat['hosts'][host]
#
#             for source, v in nat['sources'].items():
#
#                 if source not in nat_host:
#                     nat_host[source] = []
#
#                 if len(nat_host[source]) > 0:
#                     _interfaces = [i['interface'] for i in nat_host[source]]
#                 else:
#                     _interfaces = []
#
#                 for idx, interface in enumerate(interfaces, start=1):
#
#                     if len(_interfaces) == 0:
#                         rule = v['base_rule'] + idx
#                         nat_host[source].append({
#                             'description': v['description'], 'source': source,
#                             'interface': interface, 'rule': rule,
#                         })
#                         continue
#
#                     if interface not in _interfaces:
#                         rule = [i['rule'] for i in nat_host[source]][-1] + 1
#                         nat_host[source].append({
#                             'description': v['description'], 'source': source,
#                             'interface': interface, 'rule': rule,
#                         })
#
#         nat.dump()
#
#         nat_rules = {}
#         for host, v in nat['hosts'].items():
#             nat_rules[host] = {}
#             for items in v.values():
#                 for item in items:
#                     nat_rules[host][item['rule']] = {
#                         'source': item['source'],
#                         'interface': item['interface'],
#                         'description': item['description']
#                     }
#
#         self.nat = nat_rules
#
#
# class FileConf(dict):
#
#     CONFIG_DIR = "/home/{}/.cml-configvars".format(os.environ.get('USER'))
#
#     def __init__(self, file):
#         self._filepath = '{}/{}.json'.format(self.CONFIG_DIR, file)
#         try:
#             os.makedirs(self.CONFIG_DIR)
#         except FileExistsError:
#             pass
#
#         try:
#             with open(self._filepath, 'r') as f:
#                 self.update(json.load(f))
#         except FileNotFoundError:
#             pass
#
#     def dump(self):
#         if not self == self._old:
#             print("saving...%s" % self._filepath)
#             with open(self._filepath, 'w') as f:
#                 json.dump(self, f, indent=4)
#
#     def new_keys(self, new_keys):
#         for key in list(self):
#             if key not in new_keys:
#                 del self[key]
#         return self
#
#     @property
#     def _old(self):
#         try:
#             with open(self._filepath, 'r') as f:
#                 return json.load(f)
#         except FileNotFoundError:
#             return {}
#
#
# class FileConf2(dict):
#
#     CONFIG_DIR = "/home/{}/.cml-configvars".format(os.environ.get('USER'))
#
#     def __init__(self, file):
#         self._filepath = '{}/{}.json'.format(self.CONFIG_DIR, file)
#         try:
#             os.makedirs(self.CONFIG_DIR)
#         except FileExistsError:
#             pass
#
#         try:
#             with open(self._filepath, 'r') as f:
#                 self.update(json.load(f))
#         except FileNotFoundError:
#             pass
#
#         self._old_data = copy.deepcopy(self)
#
#     def dump(self):
#         if not self == self._old_data:
#             print("saving...%s" % self._filepath)
#             with open(self._filepath, 'w') as f:
#                 json.dump(self, f, indent=4)
#
#     def update_keys(self, keys):
#         for key in list(self):
#             if key not in keys:
#                 del self[key]
