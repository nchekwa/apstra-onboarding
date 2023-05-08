#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import sys
sys.dont_write_bytecode = True

import logging
logger = logging.getLogger(__name__)

import json
import yaml
import os
import pathlib
import copy
from pprint import pprint
import jsonschema
import re

class Config():
    from . import BoardingAOS
    
    def __init__(self, main_class: BoardingAOS):
        self.parameters = main_class.parameters
        self.internal = main_class.internal
  
    def _read(self, path):
        fpath = pathlib.Path(os.path.join(self.parameters.current_dir, path ))
        yaml_content = ''

        # Load anchors files
        anchor_path = os.path.dirname(fpath)
#        yaml_anchor_files = [f for f in sorted(os.listdir(anachor_path)) if (f.endswith('.yaml') and f.startswith('_'))]
        yaml_anchor_files = [f for f in sorted(os.listdir(anchor_path)) if (f.endswith('.yaml') and re.search(r'\s&\w+', open(os.path.join(anchor_path, f)).read()) )]


        for file in yaml_anchor_files:
            with open(anchor_path+"/"+file, 'r') as f:
                yaml_content += f.read()
            yaml_content += "\n\n"
        
        if os.path.isfile(fpath):
            with open(path, 'r') as f:
                yaml_content += f.read()
                
            try:
                parsed_yaml = yaml.safe_load(yaml_content)
                parsed_yaml.pop('__anchors__', None)
                #pprint(parsed_yaml)
                #parsed_yaml = yaml.load(stream, Loader=yaml.Loader)
                #print(parsed_yaml)
            except yaml.YAMLError as exc:
                #print(exc)
                return(exc)
            return(parsed_yaml)
        else:
            print("Config file not exist: "+str(path))
            exit(1)
            
    def get(self, mconfig):
        if os.path.isfile('aos.yaml'):
            apstra_config = self._read('aos.yaml')
            logger.info("Read config: ./aos.yaml")
        else:
            apstra_config = dict()
            apstra_config['aos'] = dict()
            
        if os.path.isdir(mconfig):
            self.parameters.config = apstra_config
            
            # Load and Merge YAML files
            yaml_files = [f for f in sorted(os.listdir(mconfig)) if not (f.endswith('.yaml') and f.startswith('_'))]
            for f_yaml in yaml_files:
                logger.info(f"Read config: {f_yaml}")
                self.parameters.config =  self.internal.dict_fmerge(self.parameters.config, self._read(f"{mconfig}/{f_yaml}"))
        else:
            master_config = self._read(mconfig)
            self.parameters.config =  self.internal.dict_fmerge(apstra_config, master_config)

        self.compile()
        #pprint(self.parameters.config)
        for bp_name in self.parameters.config['blueprints']:
            self.parameters.sync[bp_name] = dict()
            self.parameters.sync[bp_name]['routing-zones'] = dict()
            self.parameters.sync[bp_name]['virtual-networks'] = dict()
            self.parameters.sync[bp_name]['connectivity-templates'] = dict()
            self.parameters.sync[bp_name]['nodes'] = dict()
        return(self.parameters.config)


    def compile(self):
        # blueprints
        # will only keep bluprint[bp_name][apstra] which is not null
        # will overwrite from aos[name][bluprint](bp_name) to bluprint[bp_name][apstra]
        bp = dict()
        to_suppress = list()
        for apstra_name, value in self.parameters.config.get('aos').items():
            if value.get('blueprints'):
                for name in value['blueprints']:
                    bp[name] = apstra_name
        if self.parameters.config.get('blueprints'):
            for name, bp_value in self.parameters.config['blueprints'].items():
                if bp.get(name):
                    self.parameters.config['blueprints'][name]['apstra'] = bp.get(name)
                if bp_value.get('apstra') is None:
                    to_suppress.append(name)
        for name in to_suppress:
            del(self.parameters.config['blueprints'][name])
        
        # routing-zone
        # will use bluprint[bp_name]['parameters']['routing-zone']['vni_addend'] if vni_id is not defined
        if self.parameters.config.get('blueprints'):
            for bp_name, bp_value in self.parameters.config['blueprints'].items():
                if self.parameters.config['blueprints'][bp_name].get('routing-zones') == None:
                    self.parameters.config['blueprints'][bp_name]['routing-zones'] = dict()
                try:
                    vni_addend = self.parameters.config['blueprints'][bp_name]['parameters']['routing-zone']['vni_addend']
                except:
                    vni_addend = 0
                
                if bp_value.get('routing-zones'):
                    for rz_id, rz in enumerate(self.parameters.config['blueprints'][bp_name]['routing-zones']):
                        if self.parameters.config['blueprints'][bp_name]['routing-zones'][rz_id].get('vlan_id') == None:
                            logger.error(f"Remove routing-zone: {self.parameters.config['blueprints'][bp_name]['routing-zones'][rz_id]} as it dosnt have VLAN_id")
                            exit(1)
                            
                        if self.parameters.config['blueprints'][bp_name]['routing-zones'][rz_id].get('vni_id') == None and vni_addend > 0:
                            vlan_id = self.parameters.config['blueprints'][bp_name]['routing-zones'][rz_id]['vlan_id']
                            self.parameters.config['blueprints'][bp_name]['routing-zones'][rz_id]['vni_id'] = int(vlan_id) + int(vni_addend)
                            
                        if self.parameters.config['blueprints'][bp_name]['routing-zones'][rz_id].get('vni_id') == None and vni_addend == 0:
                            logger.error(f"Remove routing-zone: {self.parameters.config['blueprints'][bp_name]['routing-zones'][rz_id]} as it dosnt have VNI_ID")
                            exit(1)
                        
        # virtual-networks:
        # if virtual-networks is not define - create empty dict
        if self.parameters.config.get('blueprints'):
            for bp_name, bp_value in self.parameters.config['blueprints'].items():
                if self.parameters.config['blueprints'][bp_name].get('virtual-networks') == None:
                        self.parameters.config['blueprints'][bp_name]['virtual-networks'] = dict()
        
        # resource
        # will only keep resource[type] if include 'apstra' parameter
        if self.parameters.config.get('resource'):
            for rs_typ,rs_list in self.parameters.config['resource'].items():
                for i, rs in enumerate(rs_list):
                    if rs.get('apstra') is None:
                        del(self.parameters.config['resource'][rs_typ][i])
        else:
            self.parameters.config['resource'] = list()

        # routing-policies:
        # if routing-policies is not define - create empty dict
        if self.parameters.config.get('blueprints'):
            for bp_name, bp_value in self.parameters.config['blueprints'].items():
                if self.parameters.config['blueprints'][bp_name].get('routing-policies') == None:
                        self.parameters.config['blueprints'][bp_name]['routing-policies'] = list()

        # connectivity-templates
        if self.parameters.config.get('blueprints'):
            for bp_name, bp_value in self.parameters.config['blueprints'].items():
                if self.parameters.config['blueprints'][bp_name].get('connectivity-templates') == None:
                        self.parameters.config['blueprints'][bp_name]['connectivity-templates'] = list()
                        
        # nodes
        if self.parameters.config.get('blueprints'):
            for bp_name, bp_value in self.parameters.config['blueprints'].items():
                if self.parameters.config['blueprints'][bp_name].get('nodes') == None:
                        self.parameters.config['blueprints'][bp_name]['nodes'] = list()

        self.schema_validation(self.parameters.config, "schemas/schema.json")

        # replace key lables (ie. name->label)
        replace_data = {"name": "label"}
        self.parameters.config = self.replace_key(self.parameters.config, replace_data)




    def redacted(self):
        self.config_redacted = copy.deepcopy(self.parameters.config)
        for key, value in self.config_redacted['aos'].items():
            self.config_redacted['aos'][key]['password'] = "<REDACTED>"
        return(self.config_redacted)
    



    def replace_key(self, d: dict, replace_data):
        '''
        replace key lables (ie. name->label) inside nested dict
        '''
        if isinstance(d, dict):
            d_copy = d.copy()
            for k, v in d_copy.items():
                if isinstance(v, dict):
                    self.replace_key(v, replace_data)
                elif isinstance(v, list):
                    for item in v:
                        self.replace_key(item, replace_data)
                if k in replace_data:
                    new_key = replace_data[k]
                    d[new_key] = d.pop(k)
        elif isinstance(d, list):
            for item in d:
                self.replace_key(item, replace_data)
        return d
    
    
    

    def schema_validation(self, data, schema_file_path):
        with open(schema_file_path, 'r') as schema_file:
            try:
                schema = json.load(schema_file)
            except ValueError:
                schema = {}
                raise ValueError("ERROR")

        base_uri = 'file:' + os.path.abspath(os.path.dirname(schema_file_path)) + '/'
        resolver = jsonschema.RefResolver(base_uri, schema)
        validator = jsonschema.Draft7Validator(schema, resolver=resolver)
        #pprint(validator)
        try:
            validator.validate(data)
            logger.info("JSONSchema Validation successful!")
        except jsonschema.exceptions.ValidationError as error:
            logger.critical("Validation failed:")
            logger.critical(error)
            exit(1)
            
            
            
