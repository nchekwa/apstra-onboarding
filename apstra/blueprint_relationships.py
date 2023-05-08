#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import logging
logger = logging.getLogger(__name__)

from pprint import pprint
from apstra.resources import Range 
from typing import List

from apstra.errors import ErrorApstraAPI

class Relationships:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters
    
    # #################################################################################################################
    # SEARCH
    #  
    def search_relationship(self, search_value = str, search_key = "source_id"):
        return(self.apstra.rest.search_object( 
                uri             = f"/api/blueprints/{self.parameters.bp.id}/relationships",
                value           = search_value, 
                key             = search_key, 
                name            = "Relationship"
                ))

    # #################################################################################################################
    # SET / CREATE
    #
    def create_relationship(self, 
                source_id: str = None,
                target_id: str = None,
                type: str = None,
                bp_id = None
               ):
        if bp_id is None:
            bp_id = self.parameters.bp.id
            
        if target_id is None or target_id is None or type is None:
            logger.critical("Blueprint Relationships > create_relationship")
            raise ErrorApstraAPI(f"Missing {source_id} / {target_id} / {type}")

        try:
            apstra_reponse = self.apstra.rest.post_json_response(f"/api/blueprints/{bp_id}/relationships", data={"source_id": target_id, "target_id": target_id, "type": type })
        except Exception as e:
            logger.critical("Blueprint Relationships > create_relationship")
            raise ErrorApstraAPI(e)

        return(apstra_reponse)