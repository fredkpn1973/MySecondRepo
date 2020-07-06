from utils import calc_evc_str, calc_vpn_str
from jinja2 import Environment, FileSystemLoader, StrictUndefined


def _j2_parser(template_name, **kwargs):

    # Set the directory where the files can be found
    file_loader = FileSystemLoader('j2templates')

    # Environment is the basic Jinja class to create objects from

    env = Environment(loader=file_loader, trim_blocks=True,
                      lstrip_blocks=True,
                      undefined=StrictUndefined)
    template = env.get_template(template_name)
    return template.render(**kwargs)


def create_bridge_domain(vlan, sc_uu='8000', sc_m='4000', sc_b='4000',
                         mac_ag='300', mac_sec=True, l2_dom='ST', mc=False,
                         bd_desc=None):
    """ Prints ASR9000 bridge domain configuration for Schiphol network.

    Arguments:
    file --> name of file object used in "with open" context manager.
    vlan --> vlan (str)

    Keyword arguments:
    sc_uu --> Storm control unknown unicast value in pps, default = '8000'
    sc_m --> Storm control multicast value in pps, default = '4000'
    sc_b --> Storm control broadcast value in pps, default = '4000'
    mac_ag --> mac aging timer (sec) in bridge domain, default = '300'
    mac_sec --> mac securiry, if True then MAC moves are logged, default = True
    l2_dom --> Layer-2 domain. Is equal to 'ST' or 'GMI'. Used to seperate overlapping VLAN space, default ='ST'
    mc --> Multicast. If True then multicast storm control is disabled in bridge domain, default = False
    """

    evc_str = calc_evc_str(vlan, l2_dom)
    vpn_str = calc_vpn_str(vlan, l2_dom)

    kwargs = {'vlan': vlan, 'sc_uu': sc_uu, 'sc_m': sc_m, 'sc_b': sc_b, 'mac_ag': mac_ag, 'mac_sec': mac_sec,
              'mc': mc, 'evc_str': evc_str, 'vpn_str': vpn_str, 'bd_desc': bd_desc}
    return _j2_parser('bridge_domain.txt', **kwargs)


def create_add_vlan_port(vlan, intf_index, encap='Tagged', intf_desc='VLAN to VPLS VFI', l2_dom='ST'):
    """ Prints specific config of VLAN on dot1q trunk port for Schiphol network

    Arguments:
    file --> name of file object used in "with open" context manager.
    vlan --> vlan (str)
    intf_index --> name of interface on which VLAN is added

    Keyword arguments:
    encap --> if 'Tagged' then dot1q encap, if 'Untagged' then untagged "VLAN" is used, default='Tagged'
    desc --> Used for description on subinterface, default='VLAN to VPLS VFI'
    l2_dom --> Layer-2 domain. Is equal to 'ST' or 'GMI'. Used to separate overlapping VLAN space, default ='ST'    
    """

    evc_str = calc_evc_str(vlan, l2_dom)

    kwargs = {'intf_index': intf_index, 'vlan': vlan,
              'evc_str': evc_str, 'intf_desc': intf_desc}
    return _j2_parser('vlan_port.txt', **kwargs)


def create_vpn(vrf_id, vrf_desc, uni_loop_self_id=None, any_RP_loop_id=None, uni_loop_self_ip=None,
               uni_loop_other_ip=None, any_RP_loop_ip=None, dr_prio='120', mc='N'):
    """ Prints L3VPN configuration for ASR9000 in Schiphol network.

    Arguments:
    file --> name of file object used in "with open" context manager.
    vrf_id --> name of vrf, in ST network per design this equals to an integer, type is str
    vrf_desc --> description of vrf

    Keyword arguments:
    uni_loop_self_id --> index of loopback interface, used for MSDP peering.
                         If mc is set to 'N' this value will not be printed
    any_RP_loop_id --> index for loopback interface of anycast address.
                       If mc is set to 'N' this value will not be printed
    uni_loop_self_ip --> ip address of loopback used for MSDP peering.
                         If mc is set to 'N' this value will not be printed
    uni_loop_other_ip --> ip address of loopback of peer ASR9k router.
                          If mc is set to 'N' this value will not be printed
    any_RP_loop_ip --> anycast ip address. If mc is set to 'N' this value will not be printed
    dr-prio --> PIM DR prio, default = '120'. If mc is set to 'N' this value will not be printed
    mc --> Multicast. If 'Y' then multicast specific config is printed too   
    """

    kwargs = {'vrf_id': vrf_id, 'vrf_desc': vrf_desc, 'uni_loop_self_id': uni_loop_self_id,
              'any_RP_loop_id': any_RP_loop_id, 'any_RP_loop_ip': any_RP_loop_ip, 'dr_prio': dr_prio,
              'uni_loop_other_ip': uni_loop_other_ip, 'uni_loop_self_ip': uni_loop_self_ip, 'mc': mc}
    return _j2_parser('vpn.txt', **kwargs)


def create_add_bvi_hsrp(vrf_id, vlan, bvi_desc, bvi_ip, bvi_mask, hsrp_ip, bvi_peer_ip, active_router=True,
                        l2_dom='ST', mc=False, templ_type='1'):
    """ Prints BVI and corresponding HSRP configuration in Schiphol network.

    Arguments:
    file --> name of file object used in "with open" context manager.
    vrf_id --> name of vrf, in ST network per design this equals to an integer, type is str
    bvi_desc --> description of BVI
    bvi_ip --> ip address of BVI interface
    bvi_mask --> network mask of BVI interface
    hsrp_ip --> HSRP ip address
    bvi_peer_ip --> ip address of peer ASR9k router. Used for BFD config

    Keyword arguments:
    active_router --> if 'Y' then router is HSRP active forwarder else 'N'
    l2_dom --> Layer-2 domain. Is equal to 'ST' or 'GMI'. Used to seperate overlapping VLAN space, default ='ST'
    mc --> Multicast. If 'Y' then multicast specific configs are printed
    templ_type --> see here under, default ='1'

    templ_type='1' --> prints complete config
    templ_type='2' --> prints complete config, except BVI interface shut and BFD and HSRP delay missing in HSRP section
    templ_type='3' --> prints config to unshut BVI interface
    templ_type='4' --> prints config to complete HSRP section (HSRP delay and BFD)
    """

    evc_str = calc_evc_str(vlan, l2_dom)
    vpn_str = calc_vpn_str(vlan, l2_dom)

    kwargs = {'vrf_id': vrf_id, 'vlan': vlan, 'vpn_str': vpn_str, 'evc_str': evc_str,
              'bvi_desc': bvi_desc, 'bvi_ip': bvi_ip, 'bvi_mask': bvi_mask, 'hsrp_ip': hsrp_ip,
              'bvi_peer_ip': bvi_peer_ip, 'active_router': active_router, 'mc': mc, 'templ_type': templ_type}
    return _j2_parser('bvi_hsrp.txt', **kwargs)


def create_add_bvi_dhcp_profile(bvi_intf, profile_name):
    """ 
    """

    kwargs = {'bvi_intf': bvi_intf, 'profile_name': profile_name}
    return _j2_parser('bvi_dhcp_profile.txt', **kwargs)


def vlan_change_ios_xe(vlan, new_vlan, vlan_name, intf_list):

    kwargs = {'vlan': vlan, 'new_vlan': new_vlan, 'vlan_name': vlan_name,
              'intf_list': intf_list}
    return _j2_parser('vlan_change_ios_xe.txt', **kwargs)


def vlan_change_avaya_ers(vlan, new_vlan, vlan_name,
                          vlan_member_port_list, all_pvid_port_list,
                          intf_all_type, spann_tree_items, mrouter_ports):

    kwargs = {'vlan': vlan, 'new_vlan': new_vlan, 'vlan_name': vlan_name,
              'vlan_member_port_list': vlan_member_port_list,
              'all_pvid_port_list': all_pvid_port_list,
              'intf_all_type': intf_all_type,
              'spann_tree_items': spann_tree_items,
              'mrouter_ports': mrouter_ports}

    return _j2_parser('vlan_change_avaya_ers.txt', **kwargs)


if __name__ == "__main__":

    """An example here to show how to use this module
    """

    with open('Test.txt', 'w') as test:
        print(create_bridge_domain('1234'), file=test)
        print(create_add_vlan_port('1234', 'BE1.1234'), file=test)
