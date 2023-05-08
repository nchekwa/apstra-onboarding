#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import sys
sys.dont_write_bytecode = True

import logging
logger = logging.getLogger(__name__)

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import re
import copy

from typing import List, Tuple, Union, Generator
from collections import namedtuple
from pprint import pprint
from time import sleep

from apstra.dao import ActiveBlueprint, BlueprintInfo

class Blueprint:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters
    
        from apstra.blueprint_tags import Tags as ApstraBlueprintTags    
        from apstra.blueprint_routing_policies import RoutingPolicies as ApstraBluprintRoutingPolicies
        from apstra.blueprint_nodes import Nodes as ApstraBlueprintNodes
        from apstra.blueprint_cabling import Cabling as ApstraBlueprintCabling
        from apstra.blueprint_connectivity_templates import ConnectivityTemplates as ApstraBlueprintConnectivityTemplates
        from apstra.blueprint_virtual_networks import VirtualNetworks as ApstraBlueprintVirtualNetworks
        from apstra.blueprint_routing_zones import RoutingZones as ApstraBlueprintRoutingZones
        from apstra.blueprint_relationships import Relationships as ApstraBlueprintRelationships
        
        self.relationships = ApstraBlueprintRelationships(self.apstra)
        self.tags = ApstraBlueprintTags(self.apstra)
        self.connectivity_templates = ApstraBlueprintConnectivityTemplates(self.apstra)
        self.routing_policies = ApstraBluprintRoutingPolicies(self.apstra)
        self.nodes = ApstraBlueprintNodes(self.apstra)
        self.cabling = ApstraBlueprintCabling(self.apstra)
        self.virtual_networks = ApstraBlueprintVirtualNetworks(self.apstra)
        self.routing_zones = ApstraBlueprintRoutingZones(self.apstra)

    ####################################################################################################
    #
    def connect(self, bp_name: str) -> ActiveBlueprint:
        return(self.apstra.client.change_blueprint(bp_name))
    
    ####################################################################################################
    #
    def get(self, search_value: str, search_key = "label") -> BlueprintInfo:
        uri = "/api/blueprints"
        response = self.apstra.rest.search_object(search_value, search_key, uri)
        return(BlueprintInfo(**response))
        
    ####################################################################################################
    #
    def get_device_redundancy_group_mapping(self, bp_id:str = None):
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        
        if self.parameters.systems.get(bp_id):
            return(self.parameters.systems[bp_id])
        
        query = "node('redundancy_group', name='rg').out('composed_of_systems').node('system', system_type='switch', name='switch')"
        rg_list = self.apstra.rest.qe_query(query, bp_id = bp_id)
        
        query = "match(node('system', name='physical_node', system_type='switch'))"
        physical_node = self.apstra.rest.qe_query(query, bp_id = bp_id)
                
        r = dict()
        for rg in rg_list:
            switch_id           = rg['switch']['id']
            
            switch_system_id    = rg['switch']['system_id']
            switch_hostname     = rg['switch']['hostname']
            switch_label        = rg['switch']['label']
            
            rg_id               = rg['rg']['id']
            rg_label            = rg['rg']['label']
            
            r[switch_system_id]       = {'type': 'switch', 'id': switch_id, 'label': switch_label, 'hostname': switch_hostname, 'rg': {'id': rg_id, 'label': rg_label} }
            r[switch_hostname]        = r[switch_system_id]
            r[switch_label]           = r[switch_system_id]
            
            if rg_label not in r:
                r[rg_label] = {'type': 'rg' , 'id': rg_id, 'label': rg_label, 'systems': {'id': [], 'sn': [], 'label': [], 'hostname': []}}
            
            r[rg_label]['systems']['id'].append(switch_id)
            r[rg_label]['systems']['sn'].append(switch_system_id)
            r[rg_label]['systems']['label'].append(switch_label)
            r[rg_label]['systems']['hostname'].append(switch_hostname)
 
        for node in physical_node:
            node_id         = node['physical_node']['id']
            
            node_system_id  = node['physical_node']['system_id']
            node_hostname   = node['physical_node']['hostname']
            node_label      = node['physical_node']['label']
            node_role       = node['physical_node']['role']
            
            if not r.get(node_system_id):
                r[node_system_id]       = {'type': 'switch', 'role': node_role, 'id': node_id, 'hostname': node_hostname, 'label': node_label, 'rg': {'id': rg_id, 'label': rg_label} }
                r[node_hostname]        = r[node_system_id]
                r[node_label]           = r[node_system_id]

        self.parameters.systems[bp_id] = r
        return(self.parameters.systems[bp_id])
    
    ####################################################################################################
    #
    def revert(self, bp_id) -> None:
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        uri = f'/api/blueprints/{bp_id}/revert'
        apstra_reponse = self.apstra.rest.post_json_response(uri)
        return(apstra_reponse)
    


 



    
