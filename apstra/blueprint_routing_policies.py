#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import logging
logger = logging.getLogger(__name__)

from pprint import pprint


from apstra.errors import ErrorApstraAPI
from apstra.dao import RoutePolicy, AsyncResponse, HttpStatus

from dacite import from_dict
from dataclasses import asdict
from typing import Union, Tuple, List, Dict


class RoutingPolicies:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters

    # #################################################################################################################
    # SET / CREATE
    #
    def create(self, routing_policy: Union[RoutePolicy,Dict] ) -> Union[AsyncResponse,ErrorApstraAPI]:
        """
        Creates a new routing policy on the Apstra specified by the object's `apstra` attribute.

        :param routing_policy: A `RoutePolicy` object representing the new routing policy to be created.
        :type routing_policy: RoutePolicy

        :return: An `AsyncResponse` object representing the asynchronous creation of the routing policy,
                or an `ErrorApstraAPI` object representing an error that occurred during the creation process.
        :rtype: Union[AsyncResponse, ErrorApstraAPI]
        """
        if isinstance(routing_policy, RoutePolicy):
            routing_policy = asdict(routing_policy)
        
        json_to_sent = self.apstra.rest.generate_template('routing-policy', routing_policy)
        r = self.apstra.rest.post_json_response(f"/api/blueprints/{self.parameters.active_bp.id}/routing-policies", data=json_to_sent, params={"async": "full"})
        return(AsyncResponse(**r))

    # #################################################################################################################
    # GET
    #
    def get(self, search_value = None, search_key: str = "label", bp_type: str = 'staging') -> Union[RoutePolicy,None]:
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/routing-policies?type={bp_type}"
        try:
            reponse_data = self.apstra.rest.search_object(search_value, search_key, uri)
            if reponse_data is None:
                return None
        except:
            return None
        
        routing_instance = from_dict(data_class=RoutePolicy, data=reponse_data)
        return(routing_instance)

        
    def get_all(self) -> List[RoutePolicy]:
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/routing-policies"
        apstra_reponse = self.apstra.rest.get_json_response(uri)
        return_list = list()
        for data_item in apstra_reponse.get('items'):
            obj = from_dict(data_class=RoutePolicy, data=data_item)
            return_list.append(obj)
        return(return_list)
        
    # #################################################################################################################
    # DELETE
    #
    def delete(self, routing_policy: str) -> Union[HttpStatus,ErrorApstraAPI]:
        """
        Deletes the routing policy with the specified name or ID.

        :param routing_policy: The name or ID of the routing policy to delete.
        :type routing_policy: str
        
        :raises ErrorApstraAPI: If an error occurs while deleting the routing policy.
        """

        # We assume that provided 'routing_policy' is 'label' / not 'id'
        rp = self.get(routing_policy)

        if rp is None:
            # Not found name -> we assume that provided 'routing_policy' is 'id'
            routing_policy_id = routing_policy
        else:
            # Provided 'routing_policy' is a lable -> we get 'id'
            routing_policy_id = rp.id
            
        reponse = self.apstra.rest.delete_request(f"/api/blueprints/{self.parameters.active_bp.id}/routing-policies/{routing_policy_id}")
        return HttpStatus(reponse.status_code)
