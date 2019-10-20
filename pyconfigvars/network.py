import re
import json
import collections
from itertools import combinations
from random import randrange, shuffle

from netaddr import IPNetwork, IPSet, IPRange, IPAddress, EUI, mac_unix_expanded, cidr_merge
from ansible.errors import AnsibleError

from pyconfigvars.file import File


def warning(*args):
    print("\033[1;35m%s\033[0m" % " ".join([str(i) for i in args]))


def _defaultdict():
    return collections.defaultdict(_defaultdict)


class Network:

    _json_file = File('ipnetworks')
    _temp = _defaultdict()
    _global_existing_ipset = collections.defaultdict(IPSet)

    def __init__(self, cidr, _test=False, **kwargs):

        if not _test:
            self._json_file = File('_ipnetwork')

        self._ipnetwork = IPNetwork(cidr)
        self._cidr = self._ipnetwork.cidr.__str__()
        self._prefixlen = self._ipnetwork.prefixlen
        if cidr != self._cidr:
            raise AnsibleError(
                "Invalid IP network: %s is an IP address belong to %s" % (cidr, self._cidr))
        elif self._prefixlen > 30:
            raise AnsibleError(
                "Network prefix length > 30 is not supported: %s" % self._cidr)

        self._ipset = IPSet(self._ipnetwork)
        self._existing_ipset = self._global_existing_ipset[self._cidr]
        self._overlaps = None

        try:
            self._attrs = self._json_file[self._cidr]
        except KeyError:
            self._attrs = {
                'description': None,
                'parent': None,
                'is_parent': False,
                'state': None,
                **kwargs
            }

            self._json_file[self._cidr] = self._attrs

        for _cidr, _attrs in self._json_file.items():
            _ipnetwork = IPNetwork(_cidr)

            if self._cidr != _cidr:
                if self._ipnetwork.__contains__(_ipnetwork):
                    if _attrs['state'] == 'allocated':
                        self._overlaps = cidr
                        break
                    self._existing_ipset.add(_ipnetwork)
                    # warning('A*** ', self._cidr, ',', _cidr, _attrs, '\n')
                elif _ipnetwork.__contains__(self._ipnetwork):
                    self._attrs['parent'] = _cidr
                    self._global_existing_ipset[_cidr].add(self._ipnetwork)
                    # warning('B*** ', _cidr, ',', self._cidr, self._attrs, '\n')

    @property
    def _size(self):
        return self._ipnetwork.size - 2

    @property
    def _usable_ip(self):
        return self._size - 2

    @property
    def _iprange(self):
        return '{}-{}'.format(self._ipnetwork.network, self._ipnetwork.broadcast)

    @property
    def _netmask(self):
        return str(self._ipnetwork.netmask)

    @property
    def _wildmask(self):
        return str(self._ipnetwork.hostmask)

    def _check_overlaps(self):
        if self._overlaps:
            raise AnsibleError(
                'Network %s overlap with existing network %s' % (self._cidr, self._overlaps)
            )

    def iter_subnets(self, prefixlen, random=True):

        if self._attrs['state'] == 'allocated':
            raise AnsibleError('Network %s has already assign hosts' % self._cidr)
        self._check_overlaps()

        cidrs = (self._ipset - self._existing_ipset).iter_cidrs()
        subnets = [s for c in cidrs for s in c.subnet(prefixlen)]

        if random:
            shuffle(subnets)

        for subnet in subnets:
            self._existing_ipset.add(subnet)
            yield str(subnet)

    def iter_ipaddrs(self, random=True, reverse=False):

        if len(self._existing_ipset) > 0:
            raise AnsibleError("Network %s is already subnetted" % self._cidr)
        self._check_overlaps()

        try:
            self._existing_ipset.update(
                IPSet([i for i in self._json_file[self._cidr]['ipaddresses']])
            )
        except KeyError:
            pass

        ipaddrs = [i for i in IPSet(self._ipnetwork.iter_hosts()) - self._existing_ipset]

        if random:
            shuffle(ipaddrs)
        elif reverse:
            reversed(ipaddrs)

        self._attrs.update({
            'state': 'allocated',
            'ipaddresses': []})

        self._temp[self._cidr].update(self._attrs)

        for ipaddr in ipaddrs:
            self._temp[self._cidr]['ipaddresses'].append(str(ipaddr))
            self._existing_ipset.add(ipaddr)
            yield self._get_addrs(ipaddr)

    def _get_addrs(self, ipaddr):
        ip = str(ipaddr)
        prefix = '%s/%s' % (ip, self._prefixlen)
        host = '%s/32' % ip
        netmask = (ip, self._netmask)
        wildmask = (ip, self._wildmask)

        return ip, prefix, host

    def last_ip(self, incl_prefix=False):
        return self._get_addrs(IPAddress(self._ipnetwork.last - 1))

    def first_ip(self, incl_prefix=False):
        return self._get_addrs(IPAddress(self._ipnetwork.first + 1))

    def remove_subnet(self, subnet):
        for k, v in self._json_file.copy().items():
            if k == subnet and v['parent'] == self._cidr:
                del self._json_file[k]
        # del self._json_file[self._cidr]

    def _host_addr(self, addr):
        return re.sub(r'/\d+', '/32', addr)

    def remove_ipaddr(self, ipaddr):
        try:
            del self._attrs['ipaddresses'][ipaddr]
        except KeyError:
            pass

    def save(self):

        self._json_file.update(self._temp)
        self._json_file.save()


class MACAddr:

    RESERVED_MAC_ADDRESSES = '44:38:39:ff:00:00 - 44:38:39:ff:ff:ff'
    _json_file = File('mac_values')

    try:
        _json_file['_list']
    except KeyError:
        _json_file['_list'] = []

    def __init__(self):
        self._mac = self.RESERVED_MAC_ADDRESSES.split(' - ')
        self.__start, self.__end = self._mac

        self._dialect = mac_unix_expanded
        self._start = EUI(self.__start)
        self._end = EUI(self.__end)

    def iter_mac(self, random=True):

        values = set(list(range(self._start.value, self._end.value + 1)))

        uniq_values = [v for v in values - set(self._json_file['_list'])]

        if random:
            shuffle(uniq_values)

        for value in uniq_values:
            mac = EUI(value, dialect=self._dialect)
            self._json_file['_list'].append(mac.value)
            yield str(mac)

    def remove(self, mac):
        try:
            _mac = EUI(mac)
            self._json_file['_list'].remove(_mac.value)
        except TypeError:
            pass

    def save(self):
        self._json_file.save()
