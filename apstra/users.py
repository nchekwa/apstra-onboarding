#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import sys
sys.dont_write_bytecode = True

import logging
logger = logging.getLogger(__name__)

class Users:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters
    
    def search_user(self, search_value = str, search_key = "label"):
        return(self.find( 
                uri             = "/api/aaa/users", 
                value           = search_value, 
                key             = search_key, 
                name            = "User"
                ))

    def create(self, 
                username: str,
                first_name: str = None,
                last_name: str = None,
                roles: list = [],
                password: str = None, 
                email: str = None
               ):
        
        context = dict()
        context['username']     = username
        context['first_name']   = first_name
        context['last_name']    = last_name
        context['roles']        = roles
        context['password']     = password
        context['email']        = email
        
        json_to_sent = self.apstra.rest.generate_template('aaa_user', context)
        r = self.apstra.rest.post_json_response('/api/aaa/users', data=json_to_sent)
        return(r)

    def patch(self, user_id, data = dict()):
        r = self.apstra.rest.patch_json_response(f"/api/aaa/users/{user_id}", data)
        return(r)

    def delete(self,user_id):
        r = self.apstra.rest.delete_request(f"/api/aaa/users/{user_id}")
        return(r)

    def change_password(self, user_id, data = dict()):
        r = self.apstra.rest.put_json_response(f"/api/aaa/users/{user_id}/change-password", data)
        return(r)