#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import sys
sys.dont_write_bytecode = True

import logging
import json
import copy

logger = logging.getLogger(__name__)

from pprint import pprint
from .internal import ErrorApstraBoarding

RED = '\033[1;31m'
GREEN = '\033[1;32m'
GREEN0 = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[1;34m'
RESET = '\033[0m'

from apstra.dao import RoutingZone, VirtualNetwork, ObjPolicy, RoutePolicy

class Boarding:
    from . import BoardingAOS
    
    def __init__(self, main_class: BoardingAOS):
        self.parameters = main_class.parameters
        self.internal = main_class.internal
        self.apstra = main_class.apstra
        
    def run(self):
        logger.info(self.internal.generate_line(150))
        logger.info(f"START: Boarding")
        for bp_name,bp_parameters in self.parameters.config['blueprints'].items():
            aos_name = bp_parameters['apstra']
            
            self.apstra.client.connect(aos_name)
            self.apstra.client.change_blueprint(bp_name)
            
            logger.info(self.internal.generate_line(147,3))
            self.routing_zones()
            logger.info(self.internal.generate_line(147,3))
            self.virtual_network()
            logger.info(self.internal.generate_line(147,3))
            self.connectivity_template()
            logger.info(self.internal.generate_line(147,3))
            self.nodes()
            self.nodes_interface_speed()
            self.nodes_connectivity_template_assign()



    def resorces_create(self):
        logger.info(f"BOARDING: Resources")
        logger.info(self.internal.generate_line(147,3))
        for rs_type in self.parameters.config['resource']:
            if rs_type == "ip-pools":
                for rs in self.parameters.config['resource'][rs_type]:
                    self.apstra.client.connect(rs['apstra'])
                    logger.info(f"BOARDING: IPv4 Pool: {rs['label']}")
                    try:
                        self.apstra.resources.ipv4_pools.create(rs['label'], rs['subnets'])
                    except:
                        pass
            if rs_type == "vni-pools":
                for rs in self.parameters.config['resource'][rs_type]:
                    self.apstra.client.connect(rs['apstra'])
                    logger.info(f"BOARDING: VNI Pool: {rs['label']}")
                    try:
                        self.apstra.resources.vni_pools.create(rs['label'], rs['ranges'])
                    except:
                        pass
            if rs_type == "asn-pools":
                for rs in self.parameters.config['resource'][rs_type]:
                    self.apstra.client.connect(rs['apstra'])
                    logger.info(f"BOARDING: ASN Pool: {rs['label']}")
                    try:
                        self.apstra.resources.asn_pools.create(rs['label'], rs['ranges'])
                    except:
                        pass
        return('done')


    def routing_policies(self):
        for rp_data in self.parameters.config['blueprints'][self.parameters.active_bp.label].get('routing-policies'):
            # Check Sync
            try:
                sync_status = self.parameters.sync[self.parameters.active_bp.label]['routing-zones'][rp_data['label']]['status']
                apstra_graph_rp:RoutePolicy = self.parameters.sync[self.parameters.active_bp.label]['routing-zones'][rp_data['label']]['apstra_graph']
                id = apstra_graph_rp.id
            except:
                sync_status = ""
            
            if sync_status == "OK":
                logger.info(f"          RZ: {rp_data['label']}: \033[1;32mSKIP BOARDING\033[0m: Exist ID: {id} - sync status OK")
                continue
            ############
                    
            logger.info(f"BOARDING: RZ: {rp_data['label']}: Create Routing-Zones inside bluprint '{self.parameters.active_bp.label}'")
            logger.debug(f"          RZ: {rp_data}")
            
            try:
                self.apstra.blueprint.routing_policies.create(rp_data) 
            except TypeError as e:
                logger.critical(f"          ERROR: {e}")
                self.apstra.blueprint.revert(self.parameters.active_bp.id)
                raise ErrorApstraBoarding(e)
            except:
                logger.critical(f"          ERROR: Boarding Policie {rp_data}")
                logger.critical(f"          ERROR: {e}")
                self.apstra.blueprint.revert(self.parameters.active_bp.id)
                raise ErrorApstraBoarding(f"Boarding Routing Policie {rp_data}")
        return(1) 
    
    def routing_zones(self):
        for rz_data in self.parameters.config['blueprints'][self.parameters.active_bp.label].get('routing-zones'):
            #pprint(rz_data)
            #pprint(self.parameters.sync[self.parameters.active_bp.label]['routing-zones'][rz_data['label']])
            # Check Sync
            try:
                sync_status = self.parameters.sync[self.parameters.active_bp.label]['routing-zones'][rz_data['label']]['status']
                apstra_graph_rz:RoutingZone = self.parameters.sync[self.parameters.active_bp.label]['routing-zones'][rz_data['label']]['apstra_graph']
                id = apstra_graph_rz.id
            except:
                sync_status = ""
            
            if sync_status == "OK":
                logger.info(f"          RZ: {rz_data['label']}: \033[1;32mSKIP BOARDING\033[0m: Exist ID: {id} - sync status OK")
                continue
            ############
                    
            logger.info(f"BOARDING: RZ: {rz_data['label']}: Create Routing-Zones inside bluprint '{self.parameters.active_bp.label}'")
            logger.debug(f"          RZ: {rz_data}")
            
            try:
                self.apstra.blueprint.routing_zones.create(rz_data) 
            except TypeError as e:
                logger.critical(f"          ERROR: {e}")
                self.apstra.blueprint.revert(self.parameters.active_bp.id)
                raise ErrorApstraBoarding(e)
            except:
                logger.critical(f"          ERROR: Boarding Routing Zone {rz_data}")
                logger.critical(f"          ERROR: {e}")
                self.apstra.blueprint.revert(self.parameters.active_bp.id)
                raise ErrorApstraBoarding(f"Boarding Routing Zone {rz_data}")
        return(1) 
    
    
    def virtual_network(self):        
        self.apstra.blueprint.get_device_redundancy_group_mapping(self.parameters.active_bp.id)
        for vn in self.parameters.config['blueprints'][self.parameters.active_bp.label].get('virtual-networks'):
            # Check Sync
            try:
                sync_status = self.parameters.sync[self.parameters.active_bp.label]['virtual-networks'][vn['label']]['status']
                apstra_graph_vn:VirtualNetwork  = self.parameters.sync[self.parameters.active_bp.label]['virtual-networks'][vn['label']]['apstra_graph']
                id = apstra_graph_vn.id
            except:
                sync_status = ""
            
            if sync_status == "OK":
                logger.info(f"          VN: {vn['label']}: \033[1;32mSKIP BOARDING\033[0m: Exist ID: {id} - sync status OK")
                continue
            ############
            
            logger.info(f"BOARDING: VN: {vn['label']}: Create Virtual-network inside bluprint '{self.parameters.active_bp.label}'")
            logger.debug(f"          VN: {vn}")

            try:
                self.apstra.blueprint.virtual_networks.create(vn)
            except Exception as e:
                logger.critical(f"create_virtual_network:  {e}")
                raise ErrorApstraBoarding(e)
        return



    def connectivity_template(self):
        for ct_data in self.parameters.config['blueprints'][self.parameters.active_bp.label].get('connectivity-templates'):
            # Check Sync
            try:
                sync_status = self.parameters.sync[self.parameters.active_bp.label]['connectivity-templates'][ct_data['label']]['status']
                apstra_graph_ct:ObjPolicy = self.parameters.sync[self.parameters.active_bp.label]['connectivity-templates'][ct_data['label']]['apstra_graph']
                id = apstra_graph_ct.id
            except:
                sync_status = ""
            
            if sync_status == "OK":
                logger.info(f"          CT: {ct_data['label']}: \033[1;32mSKIP BOARDING\033[0m: Exist ID: {id} - sync status OK")
                continue
            ############

            logger.info(f"BOARDING: CT: {ct_data['label']}: Create Connectivity Templates inside bluprint '{self.parameters.active_bp.label}'")
            logger.debug(f"          CT: {ct_data}")

            try:
                self.apstra.blueprint.connectivity_templates.create(ct_data)
            except Exception as e:
                logger.critical(f"          ERROR: Boarding Connectivity-Template {ct_data}")
                logger.critical(f"          ERROR: {e}")
                self.apstra.blueprint.revert(self.parameters.active_bp.id)
                raise ErrorApstraBoarding(e)

    def nodes(self):
        for node_data in self.parameters.config['blueprints'][self.parameters.active_bp.label].get('nodes'):
            # Check Sync
            try:
                sync_status = self.parameters.sync[self.parameters.active_bp.label]['nodes'][node_data['label']]['status']
            except:
                sync_status = ""
            
            if sync_status == "OK":
                logger.info(f"          Node: {node_data['label']}: \033[1;32mSKIP BOARDING\033[0m: Exist - sync status OK")
                continue
            ############
            
            logger.info(f"BOARDING: Nodes for bluprint '{self.parameters.active_bp.label}'\{node_data['label']}")
            logger.debug(f"          Node: {node_data}")
                
            try:
                self.apstra.blueprint.nodes.create_node(node_data) 
            except Exception as e:
                logger.critical(f"          ERROR: Boarding Node {node_data}")
                logger.critical(f"          ERROR: {e}")
                #sself.apstra.blueprint.revert(self.parameters.active_bp.id)
                raise(e)
        return
    
    def nodes_interface_speed(self):
        apstra_nodes = self.apstra.blueprint.nodes.get_all_servers()
        
        self.apstra.blueprint.cabling.search_interface2
        for node_data in self.parameters.config['blueprints'][self.parameters.active_bp.label].get('nodes'):
            for interface in node_data['links']:
                node_ifname         = interface.get('ifname')
                node_switch         = interface['switch']
                node_switch_port    = interface['switch_port']
                node_if_speed       = interface.get('speed')
                if node_if_speed is not None:
                    node = self.apstra.blueprint.nodes.search_server(node_data['label'])
                    #pprint(node._asdict())
                    apstra_link_id = node.links[node_ifname].get('link_id')
                    apstra_link_speed = node.links[node_ifname].get('speed')
                    node_if_speed_translation = self.apstra.blueprint.cabling.speed_translation(node_if_speed)

                    if node_if_speed_translation.speed != apstra_link_speed:
                        logger.info(f"          Node: {node_data['label']}: {node_ifname} - change speed interface {node_switch}-{node_switch_port} -> {node_if_speed_translation.speed}")
                        self.apstra.blueprint.cabling.set_link_speed(apstra_link_id, node_if_speed_translation.speed)
                    return
    
    def nodes_connectivity_template_assign(self):
        node_interfaces = self.apstra.blueprint.nodes.get_node_interfaces()
        
        for node_data in self.parameters.config['blueprints'][self.parameters.active_bp.label].get('nodes'):
            node_name = node_data['label']
            for interface in node_data['links']:
                ct_list=list()
                node_ifname         = interface.get('ifname')
                node_switch         = interface['switch']
                node_switch_port    = interface['switch_port']
                node_lag_ifname     = interface.get('lag')
                
                if interface.get('ct') is not None:
                    if isinstance(interface['ct'], str):
                        ct_list.append(interface['ct'])
                    if isinstance(interface['ct'], list):
                        ct_list = interface['ct']
                        
                    for ct_name in ct_list:
                        # If LAG is defined / always apply CT to LAG and not to phisical interface
                        if node_lag_ifname is not None:
                            ct_interface_id = node_interfaces[node_name]['interfaces'][node_lag_ifname]['far_end']['id']
                        else:
                            if node_ifname is not None:
                                ct_interface_id = node_interfaces[node_name]['interfaces'][node_ifname]['far_end']['id']
                            else:
                                ct_interface_id = node_interfaces[node_switch]['interfaces'][node_switch_port]['id']

                        self.apstra.blueprint.connectivity_templates.assigne_connectivity_template(ct_name, ct_interface_id)
        return