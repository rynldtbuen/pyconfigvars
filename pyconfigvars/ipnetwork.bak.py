from itertools import combinations
from random import randrange, shuffle
import re
import json
from netaddr import IPNetwork, IPSet, IPRange, EUI, mac_unix_expanded, cidr_merge
from ansible.errors import AnsibleError
from cumulus_custom_plugins.file import File


def check_for_overlapping(a_network, b_network, **b_attrs):
    if a_network != b_attrs['parent']:
        print('**A -', a_network, b_network, b_attrs, '\n')
        raise AnsibleError(
            'a Network %s overlaps with existing network %s' % (a_network, b_network))


class Network:

    json_file = File('ipnetworks')
    json_temp = {}

    def __init__(self, cidr, **kwargs):

        self.ipnetwork = IPNetwork(cidr)
        self.cidr = self.ipnetwork.cidr.__str__()

        if cidr != self.cidr:
            raise AnsibleError(
                "Invalid IP network: %s is an IP address belong to %s"
                % (cidr, self.cidr)
            )
        elif self.ipnetwork.prefixlen > 30:
            raise AnsibleError(
                "Network prefix length > 30 is not supported: %s" % self.cidr)

        self.ipset = IPSet(self.ipnetwork)
        self.existing_ipset = IPSet()
        self.exclude_ipaddrs = [self.ipnetwork.network, self.ipnetwork.broadcast]
        self.attrs = {
            'parent': None,
            'is_parent': False,
            'state': None,
        }

        # for ipnetwork, attrs in self.json_file.items():
        #     _ipnetwork = IPNetwork(ipnetwork)
        #     _cidr = _ipnetwork.cidr.__str__()
        #
        #     if self.ipnetwork.__contains__(_ipnetwork) and self.cidr != _cidr:
        #         print('***A - ', self.cidr, _cidr, attrs, '\n')
        #
        #         if attrs['state'] is None:
        #             attrs['parent'] = self.cidr
        #             self.attrs['state'] = 'subnetted'
        #             self.attrs['is_parent'] = True
        #             print('***Ax - ', self.cidr, _cidr, attrs, '\n')
        #         # if attrs['state'] == 'allocated':
        #         #     self.json_file[self.cidr]['state'] = 'overlapping'
        #         # elif attrs['parent'] is None:
        #         #     attrs['state'] = 'merged'
        #         # elif not attrs['is_ipaddr']:
        #             # print('***A - ', self.cidr, _cidr, attrs, '\n')
        #             # attrs['parent'] = self.cidr
        #             # self.is_parent = True
        #     elif _ipnetwork.__contains__(self.ipnetwork) and self.cidr != _cidr:
        #         if attrs['parent'] is not None and attrs['is_parent']:
        #             self.attrs['parent'] = _cidr
        #             attrs['is_parent'] = True
        #             attrs['state'] = 'subnetted'
        #         elif attrs['state'] is None:
        #             self.attrs['parent'] = _cidr
        #             attrs['is_parent'] = True
        #             attrs['state'] = 'subnetted'
        #         print('***B - ', self.cidr, _cidr, attrs, '\n')
                # attrs['is_parent'] = True
                # self.parent = ipnetwork

                # if attrs['usable_ips'] is not None:
                #     raise AnsibleError(
                #         'a Network %s overlaps with existing network %s' % (self.cidr, _cidr))
                # elif attrs['is_parent']:
                #     raise AnsibleError(
                #         'a Network %s overlaps with existing network %s' % (self.cidr, _cidr))
            #     # else:
            #     #     self.existing_ipset.add(ipnetwork)
            # elif self.ipnetwork != ipnetwork and network_contains_in_self:
            #     if not attrs['is_parent']:
            #         print('***C - ', self.cidr, _cidr, attrs, '\n')
            #         raise AnsibleError(
            #             'b Network %s overlaps with existing network %s' % (self.cidr, _cidr))
            #     else:
            #         print('***B - ', self.cidr, _cidr, attrs, '\n')
            #         attrs['is_parent'] = True
            #         self.parent = _cidr
            #         self.is_subnet = True
            # elif self.ipnetwork == ipnetwork:
            #     attrs.update(**kwargs)

        self.json_file.update(self.data(cidr=self.cidr, **self.attrs))
        #
        # self.existing_ipset = IPSet([
        #     k for k, v in self.json_file.items()
        #     if v['parent'] == self.cidr
        # ])

    @property
    def subnets(self):
        return (network for network, attrs in self.json_file.items()
                if attrs['parent'] == self.cidr)

    @property
    def ipaddrs(self):
        return (network for network, attrs in self.json_file.items()
                if attrs['parent'] == self.cidr and attrs['is_ipaddr'])

    def data(self, **kwargs):
        key = kwargs['cidr']

        attrs = {
            'description': kwargs.get('description', None),
            'parent': kwargs.get('parent', None),
            'is_parent': kwargs.get('is_parent', False),
            'is_ipaddr': kwargs.get('is_ipaddr', False),
            'is_subnet': kwargs.get('is_subnet', False),
            'prefixlen': kwargs.get('prefixlen', None),
            'prefix': kwargs.get('prefix', None),
            'address': kwargs.get('address', None),
            'usable_ips': kwargs.get('usable_ip', None),
            'iprange': kwargs.get('iprange', None),
            'state': kwargs.get('state', None),
        }

        return {key: attrs}

    def iter_subnets(self, prefixlen, random=True):

        if self.attrs['iprange'] is not None:
            raise AnsibleError('%s network has already assign IP addresses' % self.cidr)

        subnets = [s for c in (self.ipset - self.existing_ipset).iter_cidrs()
                   for s in c.subnet(prefixlen)]

        if random:
            shuffle(subnets)

        self.attrs['is_parent'] = True

        for subnet in subnets:
            # self.existing_ipset.add(subnet)
            yield str(subnet)

    def iter_ipaddrs(self, prefix_type=None, random=True, exclude_list=None):

        if self.attrs['iprange'] is None and self.is_parent:
            raise AnsibleError(
                "Network %s has already have a subnets assigned" % self.cidr)

        notation = '/%s' % self.ipnetwork.prefixlen

        if prefix_type == 'host':
            notation = '/32'
        elif prefix_type == 'addr':
            notation = ''

        ipaddrs = [i for i in IPSet(self.ipnetwork.iter_hosts()) - self.existing_ipset]

        if random:
            shuffle(ipaddrs)

        self.attrs.update({
            'iprange': '{}-{}'.format(*self.exclude_ipaddrs),
            'usable_ip': len(self.ipset) - 2,
            'state': 'allocated',})

        for ipaddr in ipaddrs:

            _ipaddr = "%s%s" % (ipaddr, notation)
            self.json_temp.update(self.data(
                cidr=IPNetwork(ipaddr).__str__(),
                parent=self.cidr,
                is_ipaddr=True,
                prefixlen=self.attrs['prefixlen'],
                prefix='%s/%s' % (ipaddr.__str__(), self.attrs['prefixlen']),
                address=ipaddr.__str__()))

            self.existing_ipset.add(ipaddr)

            yield _ipaddr

    def get_ipaddr(self, index):

        if self.attrs['iprange'] is None and self.is_parent:
            raise AnsibleError(
                "Network %s has already have a subnets assigned" % self.cidr)

        notation = '/%s' % self.ipnetwork.prefixlen

        ipaddrs = [i for i in IPSet(self.ipnetwork.iter_hosts()) - self.existing_ipset]

        self.attrs.update({
            'iprange': '{}-{}'.format(*self.exclude_ipaddrs),
            'num_usable_ip': len(self.ipset) - 2})

        ipaddrs.reverse()

        for ipaddr in ipaddrs:

            _ipaddr = "%s%s" % (ipaddr, notation)
            self.json_temp.update(self.data(
                cidr=IPNetwork(ipaddr).__str__(),
                parent=self.cidr,
                is_ipaddr=True,
                prefixlen=self.attrs['prefixlen'],
                prefix='%s/%s' % (ipaddr.__str__(), self.attrs['prefixlen']),
                address=ipaddr.__str__()))

            self.existing_ipset.add(ipaddr)

            yield _ipaddr

    def remove(self):
        subnets = {k for k, v in self.json_file.items() if v['parent'] == self.cidr}
        for subnet in subnets:
            del self.json_file[subnet]
        del self.json_file[self.cidr]

    def _host_addr(self, addr):
        return re.sub(r'/\d+', '/32', addr)

    def remove_ipaddr(self, addr):
        self.json_file.remove(self.host_addr(addr))

    def save(self):
        self.json_file.update(self.json_temp)
        self.json_temp = {}

        for ipnetwork, attrs in self.json_file.copy().items():
            if attrs['state'] == 'merged':
                del self.json_file[ipnetwork]
        self.json_file.save()


class MACAddr(EUI):

    def __init__(self, addr, total=None):
        super().__init__(addr, dialect=mac_unix_expanded)
        self.total = total
        self.start = int(self)

        if total is not None:
            self.end = self.start + self.total - 1

    def __add__(self, index):
        return MACAddr(self.value + index).__str__()

    def __sub__(self, index):
        return MACAddr(self.value - index).__str__()

    def get_uniq_mac(self, existing_mac):
        for r in range(self.total):
            mac = MACAddr(self.start + r).__str__()
            if mac not in existing_mac:
                yield mac
