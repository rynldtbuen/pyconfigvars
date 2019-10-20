import os
import json
import copy
import logging


class File(dict):

    CONFIG_DIR = "/home/{}/.cml-configvars".format(os.environ.get('USER'))

    def __init__(self, file):
        self._filepath = '{}/{}.json'.format(self.CONFIG_DIR, file)
        try:
            os.makedirs(self.CONFIG_DIR)
        except FileExistsError:
            pass

        try:
            with open(self._filepath, 'r') as f:
                self.update(json.load(f))
        except FileNotFoundError:
            pass

        self.old = copy.deepcopy(self)

    # def dump(self):
    #     if not self == self.old:
    #         print("saving...%s" % self._filepath)
    #         with open(self._filepath, 'w') as f:
    #             json.dump(self, f, indent=4)

    def save(self):
        if not self == self.old:

            logging.basicConfig(
                filename='%s/%s' % (self.CONFIG_DIR, 'file.log'),
                filemode='w',
                format='%(asctime)s - %(message)s',
                level=logging.INFO,
                datefmt='%d-%b-%y %H:%M:%S'
            )
            logging.info('saving data to %s' % (self._filepath))

            print('saving... %s' % self._filepath)
            with open(self._filepath, 'w') as f:
                json.dump(self, f, indent=4)

    def remove(self, *args):

        keys = [i for arg in args for i in arg]

        try:
            for key in keys:
                del self[key]
        except KeyError:
            pass
