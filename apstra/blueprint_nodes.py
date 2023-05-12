#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import logging
logger = logging.getLogger(__name__)

from pprint import pprint
from collections import namedtuple
from typing import List, Tuple, Dict
from time import sleep

from apstra.errors import ErrorApstraAPI

class Nodes:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters
    # #################################################################################################################
    # SEARCH
    #  
    def search_node(self, value = str, key = "label", bp_id: str = None):
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/nodes"
        return self.apstra.rest.search(value, key, uri, 'Node')

    def search_system_node(self, value = str, key = "label", bp_id: str = None):
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/nodes?node_type=system"
        return self.apstra.rest.search(value, key, uri, 'Node')

    def search_server(self, value, key = "label", bp_id = None) -> List:
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        all_servers = self.get_all_servers(bp_id)
        for server in all_servers:
            if getattr(server, key) == value:
                return server
        return []
    # #################################################################################################################
    # GET
    #
    def get_all_nodes(self, node_type = None, system_type=None, bp_id: str = None):
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        #nodes = self.apstra.blueprint.get_bp_nodes(bp_id, node_type)
        
        if node_type:
            uri = f"/api/blueprints/{bp_id}/nodes?node_type={node_type}"
        else:
            uri = f"/api/blueprints/{bp_id}/nodes"

        nodes = self.apstra.rest.get_json_response(uri).get('nodes')
        
        r = list()
        for node_id in nodes:
            if system_type is not None:
                if nodes[node_id].get('system_type') != system_type:
                    continue
            r.append(nodes[node_id])
        return(r)
    
    def get_all_servers(self, bp_id=None) -> List[Tuple]:
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        
        all_servers = self.get_all_nodes(node_type='system', system_type='server', bp_id = bp_id)
        node_interfaces = self.get_node_interfaces(bp_id=bp_id)
        r = list()
        for server in all_servers:
            server['tags'] = self.apstra.blueprint.tags.get_node_tags(server['id'])
            server['links'] = node_interfaces[server['label']]['interfaces']
            d = namedtuple('Node', server.keys())
            r.append(d(**server))
            
        return(r)
    
    def get_node_interfaces(self, server: str = None,  bp_id = None) -> List|Dict:
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        devices = dict()
        devices['_id'] = dict()

        # Collect Port Channel Interfaces Details
        port_channel = dict()
        apstra_graph_ae = self.apstra.rest.qe_query('node("redundancy_group", name="redundancy_group").out("hosted_interfaces").node("interface", name="interface")')
        for po in apstra_graph_ae:
            if_id = po['interface']['id']
            port_channel.setdefault(if_id, dict())['evpn_esi_mac'] = po['interface']['evpn_esi_mac']
            port_channel[if_id]['evpn_esi_mac'] = po['interface']['evpn_esi_mac']
            
            node_id = po['redundancy_group']['id']
            node_label = po['redundancy_group']['label']
            port_channel[if_id]['system_id'] = node_id
            port_channel[if_id]['system_label'] = node_label
            port_channel[if_id]['system_role'] = 'redundancy_group'

            devices['_id'][node_id] = node_label

            devices.setdefault(node_label, dict())["system_id"] = node_id
            devices[node_label]["system_role"] = 'redundancy_group'
            
        apstra_graph_ae = self.apstra.rest.qe_query('node("interface", if_type="port_channel", name="port_channel_rg", po_control_protocol=ne(None)).out("composed_of").node("interface", name="interface").in_("hosted_interfaces").node("system", name="system")')
        for po in apstra_graph_ae:
            port_channel[if_id]['if_name'] = po['interface']['if_name']

        # Get All Interfaces
        uri = f'/api/blueprints/{bp_id}/experience/web/cabling-map?type=staging'
        apstra_graph_cabling = self.apstra.rest.get_json_response(uri, params="aggregate_links=true")

        for link in apstra_graph_cabling.get('links'):
            #pprint(link)
            for id in [0, 1]:
                if link['endpoints'][id]['system'] is not None:
                    if id == 0:
                        fe_id = 1
                    else:
                        fe_id = 0
                        
                    node_id = link['endpoints'][id]['system'].get('id') 
                    node_label = link['endpoints'][id]['system'].get('label')
                    devices['_id'][node_id] = node_label
                    
                    if_name = link['endpoints'][id]['interface'].get('if_name')
                    if if_name == None and link['type'] == 'aggregate_link':
                        if_name = link['group_label']
                    if if_name == None:
                        if_name = link['endpoints'][id]['interface']['id']
                        
                    #devices[node_label] = dict()
                    devices.setdefault(node_label, dict())["system_id"] = node_id
                    devices[node_label]["system_role"] = link['endpoints'][id]['system'].get('role')
                    
                    # Local Interface
                    devices[node_label].setdefault('interfaces', dict())[if_name] = dict()
                    for key, value in link['endpoints'][id]['interface'].items():
                        devices[node_label]['interfaces'][if_name][key] = value
                    devices[node_label]['interfaces'][if_name]["speed"] = link.get('speed')
                    devices[node_label]['interfaces'][if_name]["tags"] = link.get('tags')
                    devices[node_label]['interfaces'][if_name]["link_id"] = link.get('id')
                    if_id = devices[node_label]['interfaces'][if_name]['id']
                    devices[node_label]['interfaces'].setdefault('_id', dict())[if_id] = if_name
                    # Far End Interface
                    for key, value in link['endpoints'][fe_id]['interface'].items():
                        devices[node_label]['interfaces'][if_name].setdefault('far_end', dict())[key] = value
                    if link['endpoints'][fe_id]['system'] is not None:
                        devices[node_label]['interfaces'][if_name]['far_end']['system_id']       = link['endpoints'][fe_id]['system']['id']
                        devices[node_label]['interfaces'][if_name]['far_end']['system_label']    = link['endpoints'][fe_id]['system']['label']
                        devices[node_label]['interfaces'][if_name]['far_end']['system_role']     = link['endpoints'][fe_id]['system']['role']
                    if link['endpoints'][fe_id]['system'] is None and link['endpoints'][fe_id]['interface']['if_type'] == "port_channel":
                        ae_if_id = link['endpoints'][fe_id]['interface']['id']
                        devices[node_label]['interfaces'][if_name]['far_end']['system_id'] = port_channel[ae_if_id]['system_id']
                        devices[node_label]['interfaces'][if_name]['far_end']['system_label'] = port_channel[ae_if_id]['system_label']
                        devices[node_label]['interfaces'][if_name]['far_end']['system_role'] = port_channel[ae_if_id]['system_role']
                        devices[node_label]['interfaces'][if_name]['far_end']['evpn_esi_mac'] = port_channel[ae_if_id]['evpn_esi_mac']
        
        if server is None:
            return devices
        else:
            return devices.get(server)
    
    # #################################################################################################################
    # CREATE
    #
    def create_node(self, node_data, bp_id: str = None):
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
            bp_label = self.parameters.active_bp.label
        else:
            bp = self.apstra.blueprint.search_blueprint(bp_id, search_key='id')
            bp_label = bp.id
        
        link_data = list()
        system_id = None
        for link in node_data.get('links'):
            apstra_db = self.parameters.systems[bp_id].get(link['switch'])
            link['switch_id'] = apstra_db['id']
            link['system_id'] = system_id
            link_data.append(link)
        node_data['links'] = link_data
        
        logger.debug(f"Node Transformation: {node_data}")
        json_to_sent = self.apstra.rest.generate_template(template_name='node', context=node_data)
        logger.debug(f"JSON: {json_to_sent}")
        
        task_info = None
        try:
            uri = f"/api/blueprints/{self.parameters.active_bp.id}/switch-system-links"
            node_create = self.apstra.rest.post_json_response(uri, data=json_to_sent, params={"async": "full"})
            task_id = node_create['task_id']
        except Exception as e:
            logger.critical(f"Blueprint Nodes > create_node")
            raise ErrorApstraAPI(e, 500)
 
        my_lambda_task_to_check = lambda: self.apstra.tasks.is_task_active(task_id, bp_id) is False
        self.apstra.tasks.check_until_true(my_lambda_task_to_check, 60)
        task_info = self.apstra.tasks.get_task_by_id(task_id, bp_id)
        
        server_graphql_data = self.search_server(node_data['label'])
        if server_graphql_data.label:
            self.parameters.sync[bp_label]['nodes'][node_data['label']] = dict()
            self.parameters.sync[bp_label]['nodes'][node_data['label']]['apstra_graph'] = server_graphql_data._asdict()
            self.parameters.sync[bp_label]['nodes'][node_data['label']]['yaml'] = node_data
            self.parameters.sync[bp_label]['nodes'][node_data['label']]['status'] = 'CREATED'
        
        
        self.apply_server_interface_names(node_data['label'])
        
        # As interface name has been changed / we update self.parameters.sync
        server_graphql_data = self.search_server(node_data['label'])
        if server_graphql_data.label:
            self.parameters.sync[bp_label]['nodes'][node_data['label']]['apstra_graph'] = server_graphql_data._asdict()
            
        return task_info

    def get_node_relationships(self, relationship_type: str = None, source_id: str = None, target_id: str = None):
        uri = f'/api/blueprints/{self.parameters.active_bp.id}/relationships'
        params = {'relationship_type': relationship_type, 'source_id': source_id, 'target_id': target_id }
        return self.apstra.rest.get_json_response(uri, params=params)['relationships']
    
    def apply_server_interface_names(self, server_name, bp_id=None):
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
            bp_label = self.parameters.active_bp.label
        else:
            bp = self.apstra.blueprint.search_blueprint(bp_id, 'id')
            bp_label = bp.label

        try:
            apstra_graph = self.parameters.sync[bp_label]['nodes'][server_name]['apstra_graph']
            yaml_config = self.parameters.sync[bp_label]['nodes'][server_name]['yaml']
        except Exception as e:
            logger.critical(f"Blueprint Nodes > create_node")
            ErrorApstraAPI(f"ERROR: set_server_interface_names: {e}")
        
        links = list()
        for config_link_data in yaml_config.get('links'):
            for key, graphql_link_data in apstra_graph.get('links').items():
                if graphql_link_data.get('if_type') != 'ethernet':
                    continue
                if config_link_data.get('ifname') is None:
                    continue
                if config_link_data['switch'] == graphql_link_data['far_end']['system_label'] and config_link_data['switch_port'] == graphql_link_data['far_end']['if_name']:
                    l = {'id': graphql_link_data['id'], "endpoints": [{'interface': {'id': graphql_link_data['far_end']['id']}}, 
                                                                        {"interface": { "id": graphql_link_data['id'], "if_name": config_link_data['ifname'] } }
                                                                        ]}
                    links.append(l)

        uri = f"/api/blueprints/{bp_id}/cabling-map?comment=cabling-map-update"
        r = self.apstra.rest.patch_request(uri,data={"links": links})
        if r.status_code != 204:
            logger.error(f'Not able to change interface name for {server_name}')
            return False
        return True
    
    
    