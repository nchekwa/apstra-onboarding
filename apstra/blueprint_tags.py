#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import logging
logger = logging.getLogger(__name__)

from pprint import pprint
from apstra.resources import Range 


from apstra.errors import ErrorApstraAPI

from apstra.dao import Tag, HttpStatus


from typing import Union, Tuple, List, Dict
from dacite import from_dict
from dataclasses import asdict



class Tags:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters

    # #################################################################################################################
    # SET / CREATE
    #
    def create(self, label: str = None, description: str = "") -> Tag:            
        if label is None:
            logger.critical(f"Missing Lab: {label}")
            raise ErrorApstraAPI("Blueprint Tags > create_tag")

        r = self.apstra.rest.post_json_response(f"/api/blueprints/{self.parameters.active_bp.id}/tags", data={"description": description, "label": label}, params={"async": "full"})
        return(r)
    
    # #################################################################################################################
    # GET
    # 
    def get(self, search_value = None, search_key: str = "label", bp_type: str = 'staging') -> Union[Tag, None]:
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/tags?type={bp_type}"
        try:
            reponse_data = self.apstra.rest.search_object(search_value, search_key, uri)
            if reponse_data is None:
                return None
        except:
            return None
        
        tag = from_dict(data_class=Tag, data=reponse_data)
        return(tag)
     
    def get_all(self) -> List[Tag]:        
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/tags"
        apstra_reponse = self.apstra.rest.get_json_response(uri)
        return_list = list()
        for data_item in apstra_reponse.get('items'):
            obj = from_dict(data_class=Tag, data=data_item)
            return_list.append(obj)
        return(return_list)

    def get_by_id(self, tag_id: str) -> Union[Tag, None]:
        reponse_data = self.apstra.rest.get_json_response(f"/api/blueprints/{self.parameters.active_bp.id}/tags/{tag_id}")
        reponse = from_dict(data_class=Tag, data=reponse_data)
        return(reponse)

    def get_node_tags(self, node_id) -> List[Tag]:
        all_tags_relationship = self.apstra.blueprint.nodes.get_node_relationships(relationship_type='tag', target_id=node_id)
        r = []
        for key, rel_obj in all_tags_relationship.items():
            #pprint(rel_obj)
            tag_id = rel_obj['source_id']
            #for tag_obj in self.get(tag_id, search_key="id"):
                #obj = from_dict(data_class=Tag, data=tag_obj)
            r.append(self.get_by_id(tag_id))
                
        return r
    # #################################################################################################################
    # DELETE
    #
    def delete(self, tag_name_or_id: str) -> Union[HttpStatus,ErrorApstraAPI]:
        t = self.get(tag_name_or_id)

        if t is None:
            # Not found name -> we assume that provided 'tag' is 'id'
            tag_id = tag_name_or_id
        else:
            # Provided 'routing_policy' is a lable -> we get 'id'
            tag_id = t.id
        
        reponse = self.apstra.rest.delete_request(f"/api/blueprints/{self.parameters.active_bp.id}/tags/{tag_id}")
        return HttpStatus(reponse.status_code)
