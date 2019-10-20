import collections

from ansible.errors import AnsibleError

from ..file import File
from ..network import Network


class Interface:

    _json_file = File('interfaces')
    _static_ips = collections.defaultdict(set)
    _global_assignment = {}
    data = {}

    def __init__(self, assignment, network=None, **kwargs):

        self.network = network
        self._assignemnt
        self._ipnetwork = None
        self._ipaddr = None

        if self.network is not None:
            self._ipnetwork = Network(self.network, **kwargs)
            self._ipaddr = self._ipnetwork.iter_ipaddrs()

    def add(self, host, interface, type, id=None, ipaddr=None, **kwargs):

        try:
            assignment = self._global_assignment[host][interface]
            if assignment != self._assignment:
                raise AnsibleError(
                    'Interface %s already assign in %s' % (interface, self._assigment)
                )
        except KeyError as err:
            if str(err) == host:
                self._global_assignment.setdefault(host, {})

            self._global_assignment[host][interface] = self._assignment
        if id is None:
            id = '%s:%s' % (interface, 0)

        if ipaddr is not None:
            if ipaddr in self.static_ips[host]:
                AnsibleError('IP address already exist: %s' % ((ipaddr, interface, host)))
            self._static_ips[host].add(ipaddr)
        else:
            if type == 'unnumberred':
                ipaddr = None
            else:
                ipaddr = self._get_ipaddr(host, id, type)

        self._set_data(
            host=host,
            interface=interface,
            ipaddr=ipaddr,
            type=type,
            **kwargs
        )

    def _get_ipaddr(self, host, id, type):
        try:
            ipaddr = self._json_file[host][id]
        except KeyError:
            _ip, _prefix, _host = next(self._ipaddr)
            ipaddr = _host if type == 'looback' else _prefix
            self._set_json_file(
                host=host,
                id=id,
                ipaddr=ipaddr,
            )

        return {ipaddr: id}

    def _set_json_file(self, host, id, ipaddr):
        try:
            ipaddr = self._json_file[host][id]
        except KeyError:
            self._json_file.setdefault(host, {})[id] = ipaddr

    def _set_data(self, host, interface, **kwargs):
        attrs = {
            'host': host,
            'name': interface,
            'description': kwargs.get('alias'),
            'type': kwargs.get('type'),
            'protocol': kwargs.get('protocol'),
            'vrf': kwargs.get('vrf'),
            'ipaddresses': kwargs.get('ipaddr'),
            'neighbor': {
                'interface': kwargs.get('ninterface'),
                'host': kwargs.get('nhost'),
                'ipaddress': kwargs.get('nipaddress')
            },
            'hwaddr': kwargs.get('hwaddr')
        }

        try:
            attrs = self.data[host][interface]
            attrs['ipaddresses'].update(kwargs['ipaddr'])
        except KeyError:
            self.data.setdefault(host, {}).setdefault(interface, {}).update(attrs)

    def remove(self, host, id):
        del self._json_file[host][id]

    def save(self):

        self._json_file.save()
