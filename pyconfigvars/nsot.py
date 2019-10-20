import subprocess
import collections
import re

# def nsot_cli(resource, type, opts):
#     _cmd = cmd.split(' ')
#     try:
#         subprocess.run(
#             _cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
#     except subprocess.CalledProcessError:
#         return


def nsot_cli(command):

    cmd = ('nsot ' + command).split(' ')

    if 'list' in cmd:
        try:
            run = subprocess.run(cmd, stdout=subprocess.PIPE)

            return run.stdout.decode('utf-8').splitlines()
        except subprocess.CalledProcessError:
            return

    try:
        # subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(cmd, stdout=subprocess.PIPE, check=True)

    except subprocess.CalledProcessError:
        return


class NSoT_Attributes:

    def __init__(self, resource, attributes):

        self.resource = resource
        self.attributes = attributes

    def update(self):

        attributes = nsot_cli('attributes list -N')

        _attributes = {}

        for item in attributes:
            k, v = item.split(':')
            _attributes.setdefault(k.lower(), []).append(v)

        for attrib in self.attributes:
            if attrib not in _attributes[self.resource]:
                nsot_cli('attributes add -r %s -n %s' % (self.resource, attrib))


# class NSoT_Device:
#
#     ATTRIBUTES = [
#         'group'
#     ]
#
#     def __init__(self, data):
#
#         self.data = data
#
#         NSoT_Attributes('device', self.ATTRIBUTES).update()
#
#     def update(self):
#
#         devices = self.devices()
#
#         for host, attributes in self.data.items():
#             if host not in devices:
#                 for k, v in attributes.items():
#                     nsot_cli('devices add -H %s -a %s=%s' % (host, k, v))
#                 continue
#
#             for k, v in attributes.items():
#                 if k not in devices[host]:
#                     nsot_cli('devices update -H %s --delete-attributes -a %s=%s' % (host, k, v))
#
#         for host, attributes in devices.items():
#             if host not in self.data:
#                 nsot_cli('devices remove -H %s' % host)
#
#     def devices(self):
#
#         devices = {}
#         for item in nsot_cli('devices list -g'):
#             host, attributes = item.split(' ')
#             k, v = attributes.split('=')
#
#             devices.setdefault(host, {}).update({k: v})
#
#         return devices
#
#
# class nsot_interface:
#
#     def __init__(self, data, cidr, **kwargs):
#
#         self.data = data
#         self.network = nsot_network(cidr, **kwargs)
#         self.network.update()
#
#         # if len(kwargs) > 0:
#         #     NSoT_Attributes('network', list(kwargs)).update()
#
#     def update(self):
#
#         interfaces = self.get()
#         ip = self.network.get_ips()
#
#         ips = []
#         for host, interface in self.data.items():
#             if host not in interfaces:
#                 addr = next(ip)
#                 nsot_cli('interfaces add -D %s -n %s -c %s' % (host, interface, addr))
#                 ips.append(addr)
#                 continue
#
#             if interface not in interfaces[host]:
#                 addr = next(ip)
#                 nsot_cli('interfaces add -D %s -n %s -c %s' % (host, interface, addr))
#                 ips.append(addr)
#
#         for host, _interfaces in interfaces.items():
#             if host not in self.data:
#                 id = [v['id'] for k, v in _interfaces.items()][0]
#                 nsot_cli('interfaces remove -i %s' % id)
#                 continue
#
#             for interface, attrib in _interfaces.items():
#                 x = attrib['addresses'].replace("[u'", '').replace("']", '')
#                 ips.append(x)
#
#         for net, attrib in self.network.get().items():
#             if net not in ips and attrib['is_ip']:
#                 nsot_cli('networks remove -c %s' % net)
#
#     def get(self):
#
#         interfaces = collections.defaultdict(dict)
#
#         for item in nsot_cli('interfaces list -g'):
#             host_interface, attributes = item.split(' ')
#             host, interface = host_interface.split(':')
#             k, v = attributes.split('=')
#
#             interfaces[host].setdefault(interface, {}).update({k: v})
#
#         return interfaces
#
#
# class nsot_network:
#
#     def __init__(self, cidr, **kwargs):
#
#         self.cidr = cidr
#         self.attributes = kwargs
#
#         NSoT_Attributes('network', list(self.attributes)).update()
#
#     def update(self):
#
#         networks = self.get()
#
#         if self.cidr not in networks:
#             for k, v in self.attributes.items():
#                 nsot_cli('networks add -c %s -a %s=%s' % (self.cidr, k, v))
#
#         # for k, v in self.attributes.items():
#         #     if k not in networks[self.cidr]:
#         #         nsot_cli('networks update -c %s --delete-attributes %s=%s' % (cidr, k, v))
#
#     def get(self):
#
#         networks = {}
#         try:
#             for item in nsot_cli('networks list -g'):
#                 host, attributes = item.split(' ')
#                 k, v = attributes.split('=')
#
#                 networks.setdefault(host, {}).update({k: v})
#             return networks
#         except ValueError:
#             return networks
#
#     # def get_networks(self, prefixlen, num):
#     #
#     #     cmd = 'nsot networks list -c %s next_network -p %s -n %s' % (self.network, prefixlen, num)
#     #     networks = nsot_query(cmd)
#     #
#     #     return (n for n in networks)
#
#     def get_ips(self):
#         addrs = nsot_cli('networks list -c %s next_address -n %s' % (self.cidr, 100))
#
#         return (addr for addr in addrs)
