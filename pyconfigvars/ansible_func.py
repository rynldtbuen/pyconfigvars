import difflib
import re

from ansible.utils.color import stringc


def get_run_block_config(config, regex):
    ''' Return a block of running config '''

    return [i.group() for i in re.finditer(regex, config)]


def get_diff_commands(running, intent, dev_os):
    '''
    Args:
        running: list of device running commands
        intent: list of device intent commands
        style: device CLI command style, example, set-style

    Return: a diff of running and intent config
    '''

    style = {
        'cumulus': 'net',
        'vyos': 'set'
    }

    _diff = difflib.unified_diff(
        sorted(running), sorted(intent), fromfile='running', tofile='intent', lineterm="")
    diff = []

    for item in _diff:
        if item.startswith('+%s' % style[dev_os]):
            diff.append(stringc(item, 'green'))
        elif item.startswith('-%s' % style[dev_os]):
            diff.append(stringc(item, 'red'))
        elif item.startswith(' '):
            diff.append(stringc(item, 'normal'))
        else:
            diff.append(stringc(item, 'blue'))

    return diff
