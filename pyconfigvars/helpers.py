import re
from itertools import groupby, permutations


# def print_warning(*args):
#     print("\033[1;35m%s\033[0m" % " ".join([str(i) for i in args]))

def get_id(value):
    '''
    Return a tuple that contains a basename and id of the value.
    Example: leaf0001
    Return: ('leaf000', 1)
    '''
    c = re.compile(r'(?P<name>\S+|)(?<!(\d|-|\.))(?P<zero>0{1,}|)(?P<id>\d+.*)')
    m = re.match(c, value)
    return m.group('name') + m.group('zero'), m.group('id')


def natural_keys(v):
    def convert(v):
        return int(v) if v.isdigit() else v
    return [convert(c) for c in re.split('(\\d+)', v)]


def arrange_by(regex, _list):

    a, b = [], []
    for item in _list:
        search = re.search(regex, item)
        a.insert(0, item) if search else b.append(item)
    return sorted(a) + b


def uncluster(v, raw=False):
    try:
        _v = [i.strip() for i in v.split(',')]
    except AttributeError:
        _v = [i.strip() for i in v]

    _uncluster = []
    for item in _v:
        name, _id = get_id(item)
        id = _id.split('-')
        try:
            start, end = id
            if '.' in start:
                num, _start = start.split('.')
                _uncluster.extend(
                    [(name, '%s.%s' % (num, r)) for r in range(int(_start), int(end) + 1)])
            else:
                _uncluster.extend(
                    [(name, r) for r in range(int(start), int(end) + 1)])
        except ValueError:
            _uncluster.append((name, id[0]))

    if raw:
        return _uncluster

    return sorted([i[0] + str(i[1]) for i in _uncluster], key=natural_keys)


def glob_to_uncluster(glob):
    '''
    Append the basename of the clustered value.
    Example: vni1000-1001,1005-1006,vx1010-1030,1050-1100
    Return: ['vni1000-1001', 'vni1005-1006', 'vx1010-1030', 'vx1050-1100']
    '''
    _glob = glob.split(',')
    _list = []
    for idx, item in enumerate(_glob):
        name, id = get_id(item)
        while name == '':
            idx -= 1
            try:
                name = get_id(_glob[idx])[0]
            except IndexError:
                name = ''
                break
        _list.append(name + id)
    return uncluster(_list)


def cluster(v, start_name=True):
    _uncluster = uncluster(v, raw=True)
    _cluster = []
    for k, v in groupby(sorted(_uncluster), lambda x: x[0]):
        ids = set([int(i[1]) for i in v])
        cluster_ids = []
        for _k, _v in groupby(enumerate(sorted(ids)), lambda x: x[1] - x[0]):
            group = [i[1] for i in list(_v)]
            if len(group) > 1:
                cluster_ids.append(("{}-{}".format(group[0], group[-1])))
            else:
                cluster_ids.append(("{}".format(group[0])))
        _cluster.append((k, cluster_ids))

    if not start_name:
        return ",".join([k + ",".join(v) for k, v in _cluster])

    return ",".join([k + i for k, v in _cluster for i in v])


class network_link:
    '''
    Trasform a link string format into a stuctured data
    Example: 'spine[1-2]:swp1 -- leaf[1-4]:swp21'
    '''

    IP_INTERFACE_TYPE = ['ip', 'sub_interface']

    def __init__(self, network, links, type=None, vrf=None, protocol=None):
        self.network = network
        self.links = links
        self.type = type if type is not None else 'unnumbered'
        self.vrf = vrf
        self.protocol = protocol

        self.data()

    def _get_interface(self, interface, oper):

        interface_id = int(re.split('(\\d+)', interface)[-2])
        return uncluster("{}-{}".format(interface, interface_id + oper - 1))

    def _get_hosts(self, host_pattern):
        c = re.compile(r'(?P<name>[\s\S]+)(?:\[)(?P<start>\d+)\D(?P<end>\d+)')
        m = re.match(c, host_pattern)
        hosts = []
        if m:
            name, start, end = m.group('name'), int(m.group('start')), int(m.group('end'))
            for r in range(start, end + 1):
                hosts.append(name + str(r))
        else:
            hosts.append(host_pattern)
        return hosts

    def _get_links(self, link):
        link_perm = [
            x for x in permutations([i.strip() for i in link.split('--')])]

        for item in link_perm:
            dev_a, a_iface, dev_b, b_iface = [x for i in item for x in i.split(':')]

            a_hosts = self._get_hosts(dev_a)
            b_hosts = self._get_hosts(dev_b)
            a_interfaces = self._get_interface(a_iface, + len(b_hosts))
            b_interfaces = self._get_interface(b_iface, + len(a_hosts))

            for idx0, host in enumerate(a_hosts):
                for idx1, re_host in enumerate(b_hosts):
                    yield host, a_interfaces[idx1], re_host, b_interfaces[idx0]

    def data(self):
        data = []
        is_ip_link = True if self.type in self.IP_INTERFACE_TYPE else False
        for link in self.links:
            _links = list(self._get_links(link))
            link_ids = [
                "{0}:{1} -- {2}:{3}".format(*i) for i in _links[:len(_links) // 2]]

            for item in _links:
                host, iface, re_host, re_iface = item
                host_link = "{0}:{1} -- {2}:{3}".format(*item)

                if host_link in link_ids:
                    link_id = host_link
                    is_link_id = True
                else:
                    link_id = "{2}:{3} -- {0}:{1}".format(*item)
                    is_link_id = False

                data.append({
                    'host': host, 'interface': iface,
                    'remote_host': re_host, 'remote_interface': re_iface,
                    'network': self.network, 'type': self.type,
                    'original_link': link, 'alias': host_link,
                    'link_id': link_id, 'is_link_id': is_link_id,
                    'is_ip_link': is_ip_link, 'vrf': self.vrf,
                    'protocol': self.protocol
                })

        self.data = data

    def link_ids(self):
        return [i['link_id'] for i in self.data if i['is_link_id']]
