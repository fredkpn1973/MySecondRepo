import re
import os
import shutil
import pathlib
import fnmatch


class ReSearcher(object):
    """
    Helper  to enable evaluation
    and regex formatting in a single line
    """
    match = None

    def __call__(self, pattern, string):
        self.match = re.search(pattern, string)
        return self.match

    def __getattr__(self, name):
        return getattr(self.match, name)


class Tree(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value


def splitrange(raw_range):

    """
    ex. splitrange('105-107') will return ['105','106','107']
    """

    m = re.search(r'^(\d+)\-(\d+)$', raw_range)
    if m:
        first = int(format(m.group(1)))
        last = int(format(m.group(2)))
        return [str(i) for i in range(first, last+1)]


def calc_evc_str(vlan, l2_dom):
    """
    helper function to calculate EVC string used in
    ST ASR network.

    For example:
    ST vlan 30 --> 00030
    GMI vlan 30 --> 10030
    """

    evc_str = None

    if l2_dom == 'ST':
        if len(vlan) == 1:
            evc_str = '0000' + vlan
        elif len(vlan) == 2:
            evc_str = '000' + vlan
        elif len(vlan) == 3:
            evc_str = '00' + vlan
        elif len(vlan) == 4:
            evc_str = '0' + vlan
    elif l2_dom == 'GMI':
        evc_str = str(int(vlan) + 10000)

    return evc_str


def calc_vpn_str(vlan, l2_dom):
    """ Used in BGP part of bridge-domain configuration """
    if l2_dom == 'ST':
        vpn_id = vlan
    elif l2_dom == 'GMI':
        vpn_id = str(int(vlan) + 10000)

    return vpn_id


def move_to_dir(src, dst, pattern='*'):
    """
    Function moves files from source to destination folder based on pattern
    of filename
    """
    if not os.path.isdir(dst):
        pathlib.Path(dst).mkdir(parents=True, exist_ok=True)
    for file in fnmatch.filter(os.listdir(src), pattern):
        shutil.move(os.path.join(src, file), os.path.join(dst, file))


def get_asr_by_name(asrinfo, hostname):
    for asr in asrinfo:
        if asr["hostname"] == hostname:
            return asr





