#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import logging
logger = logging.getLogger(__name__)

from pprint import pprint
from collections import namedtuple
from apstra.resources import Range 
from typing import List, Dict, Tuple

from apstra.errors import ErrorApstraAPI

class Cabling:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters
        
    # #################################################################################################################
    # SEARCH
    #  
    def search_interface2(self, search_value = str, search_key = "label"):
        return(self.apstra.rest.search_object( 
                uri             = f"/api/blueprints/{self.parameters.bp.id}/nodes",
                value           = search_value, 
                key             = search_key, 
                name            = "Interface"
                ))
    
    # #################################################################################################################
    # GET
    # 
    def speed_translation(self, speed:str = "10G") -> Tuple:
        Speed = namedtuple('Speed', ['unit', 'value', 'speed'])
        s = Speed('G', "1", "1G")
        
        if str(speed).endswith("G"):
            s = Speed('G', int(speed[:-1]), str(speed))
            
        if str(speed).endswith("M"):
            s = Speed('M', int(speed[:-1]), str(speed))
            
        if isinstance(speed, int) and speed == 10:
            s = Speed('M', 10, '10M')
            
        if isinstance(speed, int) and speed == 100:
            s = Speed('M', 100, '100M')
            
        if isinstance(speed, int) and speed > 1000 and speed in ["1000", "10000", "25000", "40000", "50000", "100000", "200000", "400000"]:
            b = int(speed)/1000
            s = Speed('G', b, f"{b}G")
            
        return s
        
    # #################################################################################################################
    # SET
    #   
    def set_link_speed(self, link_id: str, speed: str, bp_id: str = None):
        if bp_id is None:
            bp_id = self.parameters.bp.id
        
        speed = self.speed_translation(speed)
        
        data_to_send = dict()
        data_to_send['links'] = list()
        
        link = dict()
        link['speed'] = dict()
        link['speed']['unit'] = speed.unit
        link['speed']['value'] = int(speed.value)
        link['link_id'] = link_id
        
        data_to_send['links'].append(link)
        
        try:
            url = f'/api/blueprints/{bp_id}/set-switch-system-link-speed'
            apstra_response = self.apstra.rest.put_request(url, data=data_to_send)
        except Exception as e:
            logger.critical("Bluepring Cabling > set_link_speed")
            raise ErrorApstraAPI(e)
        
        return apstra_response