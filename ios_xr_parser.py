import os
import re
import json
from glob import glob
from multiprocessing import Pool
from utils import ReSearcher, Tree


def ios_xr_parser(configfile):
    """
    Functions reads list of ASR9000 configurations and returns
    nested dictionary with service configuration data.

    :param asr_list: ASR9000 configuration file
    :return: Nested dict with configuration data
    """

    match = ReSearcher()

    with open(configfile, 'r') as f:
        lines = f.readlines()

    asr = Tree()
    context = ''

    for line in lines:
        line = line.rstrip()

        # interface info
        if match(r'^interface (.*)\.(\d+) l2transport$', line):
            context = ''
            if_index = format(match.group(1))
            vid = format(match.group(2))
            asr['portinfo'][if_index].setdefault(
                'vlan_list', []).append(vid)

        elif match(r'^interface (\S*Ether\S*|\S*GigE\S*)', line):
            port = format(match.group(1))
            context = 'port'

        elif match(r'^interface (BVI\d+)$', line):
            port = format(match.group(1))
            context = 'port'

        # evpninfo
        elif match(r'^evpn$', line):
            context = 'evpn'

        # ICCP redundancy
        elif match(r'^\s{1}redundancy$', line):
            context = 'l2vpn_iccp'

        # Bridge domain items
        elif match(r'^\s{2}bridge-domain (\w+_\d+_BD)$', line):
            bd = format(match.group(1))
            match1a = re.search(r'\s{2}bridge-domain \w+_(\d+)_BD$', line)
            evc_id = str(int(format(match1a.group(1))))
            asr['l2bd_info'][bd]['evc_id'] = evc_id
            context = 'l2_bd'

        # MSDP items
        elif match(r'^router msdp', line):
            context = 'msdp'

        # DHCP items
        elif match(r'^dhcp ipv4$', line):
            context = 'dhcp'

        # HSRP items
        elif match(r'^interface PTP0/RP0/CPU0/0|^router hsrp$', line):
            context = 'hsrp'

        # VRF Items
        elif match(r'^vrf (\d+)', line):
            context = 'vrf'

        # General info items
        elif match(r'^hostname (.*)', line):
            hostname = format(match.group(1))
            asr['hostname'] = hostname

        if context == 'port':

            if match(r'^!$', line):
                context = ''

            elif match(r'^ description (.*)$', line):
                asr['portinfo'][port]['desc'] = format(match.group(1))

            elif match(r'^ bundle id (\d+) mode (\w+)', line):
                bundle_id = format(match.group(1))
                bundle_mode = format(match.group(2))
                asr['portinfo'][port]['bundle_id'] = bundle_id
                asr['portinfo'][port]['bundle_mode'] = bundle_mode

            elif match(r'\s{1}ipv4 address (.*) (.*)', line):
                ipv4_add = format(match.group(1))
                ipv4_mask = format(match.group(2))
                asr['portinfo'][port]['ipv4_add'] = ipv4_add
                asr['portinfo'][port]['ipv4_mask'] = ipv4_mask

            elif match(r'^\s{1}vrf (.*)$', line):
                vrf = format(match.group(1))
                asr['portinfo'][port]['vrf'] = vrf
                if 'BVI' in port:
                    bvi_index = port.split('BVI')[1]

        elif context == 'l2_bd':

            if match(r'^\s{3}interface (.*)', line):
                if_index = format(match.group(1))
                asr['l2bd_info'][bd].setdefault(
                    'intf_list', []).append(if_index)

            elif match(r'^\s{3}storm-control unknown.* pps (\d+)$', line):
                asr['l2bd_info'][bd]['sc_uu'] = format(match.group(1))

            elif match(r'^\s{3}storm-control broadcast pps (\d+)$', line):
                asr['l2bd_info'][bd]['sc_bc'] = format(match.group(1))

            elif match(r'^\s{3}storm-control multicast pps (\d+)$', line):
                asr['l2bd_info'][bd]['sc_mc'] = format(match.group(1))

            elif match(r'^\s{3}evi (\d+)$', line):
                asr['l2bd_info'][bd]['evi'] = format(match.group(1))

            elif match(r'^\s{5}time (\d+)$', line):
                asr['l2bd_info'][bd]['mac_aging'] = format(match.group(1))

            elif match(r'^\s{4}secure$', line):
                asr['l2bd_info'][bd]['mac_add_sec'] = 'secure'

            elif match(r'^\s{3}vfi (EVC.*)$', line):
                asr['l2bd_info'][bd]['vfi'] = format(match.group(1))

            elif match(r'^\s{3}description (.*)$', line):
                asr['l2bd_info'][bd]['desc'] = format(match.group(1))

            elif match(r'^\s{3}routed interface BVI(\d+)$', line):
                if_idx = format(match.group(1))
                asr['l2bd_info'][bd].setdefault(
                    'intf_list', []).append('BVI' + if_idx)

            elif match(r'^\s{2}!$', line):
                context = ''

        elif context == 'evpn':

            if match(r'^\s{1}evi (\d+)$', line):
                evi_id = format(match.group(1))
                asr['evpninfo']['evi_' + evi_id]['evi_id'] = evi_id

            elif match(r'^\s{1}interface (.*)', line):
                intf = format(match.group(1))

            elif match(r'^\s{3}identifier type 0 (.*)', line):
                evpn_type_0 = format(match.group(1))
                asr['evpninfo'][intf]['evpn_iden_type_0'] = evpn_type_0

            elif match(r'^\s{2}core-isolation-group (\d+)', line):
                core_iso_grp = format(match.group(1))
                asr['evpninfo'][intf]['core_iso_grp'] = core_iso_grp

            elif match(r'^!$', line):
                context = ''

        elif context == 'l2vpn_iccp':

            if match(r'\s{2}iccp group (\d+)$', line):
                iccp_red_grp = format(match.group(1))

            elif match(r'^\s{3}interface (.*Ether.*)', line):
                if_index = format(match.group(1))
                asr['l2iccp_info'][iccp_red_grp].setdefault(
                    'intf_list', []).append(if_index)

            elif match(r'^\s{2}!$', line):
                context = ''

        elif context == 'msdp':

            if match(r'^\s{1}vrf (.*)$', line):
                vrf = format(match.group(1))
                asr['msdpinfo'].setdefault('vrf_list', []).append(vrf)

            elif match(r'^!$', line):
                context = ''

        elif context == 'dhcp':

            if match(r'^\s{1}interface (.*) relay profile (.*)', line):
                intf_index = format(match.group(1))
                profile_name = format(match.group(2))
                asr['dhcp_int_info'][intf_index] = profile_name

            elif match(r'^!$', line):
                context = ''

        elif context == 'hsrp':

            if match(r'\s{1}interface (BVI\d+)', line):
                port = format(match.group(1))

            elif match(r'\s{4}address (.*) secondary', line):
                sec_address = format(match.group(1))
                asr['hsrpinfo'][port].setdefault(
                    'sec_address', []).append(sec_address)

            elif match(r'\s{4}address (.*)', line):
                address = format(match.group(1))
                asr['hsrpinfo'][port]['address'] = address

            elif match(r'\s{4}priority (\d+)', line):
                prio = format(match.group(1))
                asr['hsrpinfo'][port]['prio'] = prio

            elif match(r'\s{4}bfd fast-detect peer ipv4 (.*)', line):
                bfd_peer = format(match.group(1))
                asr['hsrpinfo'][port]['bfd_peer'] = bfd_peer

            elif match(r'^!$', line):
                context = ''

        elif context == 'vrf':
            if match(r'^vrf (.*)', line):
                vrf_id = format(match.group(1))
                asr['vrf'].setdefault('vrf_list', []).append(vrf_id)
            elif match(r'^!$', line):
                context = ''

    return asr


def main():

    base_dir = os.getcwd()
    config_dir = base_dir + '\\Configs 4-6-2020'
    os.chdir(config_dir)

    configfiles = [configfile for configfile in glob('*.spn.local.txt')
                   if 'AGG' in configfile or 'SB' in configfile]
    pool = Pool()
    asr_info = pool.map(asr9000_configreader, configfiles)

    with open('asr_info.json', 'w') as f:
        json.dump(asr_info, f, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()
