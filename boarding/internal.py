#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import sys
sys.dont_write_bytecode = True

import logging
logger = logging.getLogger(__name__)

import uuid
import time
import os
import pathlib
import colorlog
import re
import json
import yaml

import http.client
from dataclasses import is_dataclass, asdict, fields

colorlog.default_log_colors

class Internal:
    from . import BoardingAOS
    def __init__(self, main_class: BoardingAOS):
        self.parameters = main_class.parameters
        self.handlers = main_class.handlers
        
    def get_id(self):
        if self.parameters.id == None:
            self.parameters.id = f"{int(time.time())}-{str(uuid.uuid4())}"
            #self.parameters.id = "abc"
        return(self.parameters.id)
    
    def logger(self, stdout_lvl='INFO', logfile_lvl='DEBUG'):
        self.parameters.log.path = pathlib.Path()/"logs" 
        if not os.path.isdir(self.parameters.log.path): 
            self.parameters.log.path.mkdir(parents=True, exist_ok=True) 
        
        self.parameters.log.file_path = f"{self.parameters.log.path}/{self.parameters.id}.log"
        
        # '%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s'
        #logFormatStr = '%(asctime)s | %(levelname)s | PID%(process)s | %(request_id)s | %(module)s | %(pathname)s:%(lineno)d | %(message)s'
        logger = logging.getLogger('')
        logger.setLevel(getattr(logging, logfile_lvl))

        # LOGGER> On Screen
        stdout = logging.StreamHandler(sys.stdout)
        stdout.setLevel(getattr(logging, stdout_lvl))
        stdout.setFormatter(colorlog.ColoredFormatter('%(log_color)s[%(levelname)08s] %(message)s'))
        logger.addHandler(stdout)
        
        # LOGGER > To File
        class MyFormatter(logging.Formatter):
            def format(self, record):
                # Remove colots codding
                record.msg = re.sub('\x1b\[[0-9;]*m', '', record.msg)
                record.msg = re.sub(r'\033\[[^m]*m', '', record.msg)
                return super(MyFormatter, self).format(record)

        fh_formatter = MyFormatter('%(asctime)s.%(msecs)05d | %(filename)s.%(funcName)s:%(lineno)d | %(levelname)08s | %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
        fh = logging.FileHandler(self.parameters.log.file_path)
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)

        logger.info(f"Start: {int(time.time())}")
        logger.info(f"ID: {self.parameters.id}")

        self.handlers.logger = logger
        return(logger)
    
    def save_parameters(self):
        with open(f"{self.parameters.log.path}/{self.parameters.id}_config_json.txt", 'w', encoding='utf-8') as f:
            json.dump(self.parameters.config, f, indent=4)
        with open(f"{self.parameters.log.path}/{self.parameters.id}_config_yaml.txt", 'w', encoding='utf-8') as f:
            yaml.dump(self.parameters.config, f)
        with open(f"{self.parameters.log.path}/{self.parameters.id}_sync_json.txt", 'w', encoding='utf-8') as f:
            sync_as_dict = self.convert_to_dict(self.parameters.sync)
            json.dump(sync_as_dict, f, indent=4)
            
    def dict_fmerge2(self, base_dct, merge_dct, add_keys=True):
        rtn_dct = base_dct.copy()
        if add_keys is False:
            merge_dct = {key: merge_dct[key] for key in set(rtn_dct).intersection(set(merge_dct))}

        rtn_dct.update({
            key: self.dict_fmerge(rtn_dct[key], merge_dct[key], add_keys=add_keys)
            if isinstance(rtn_dct.get(key), dict) and isinstance(merge_dct[key], dict)
            else merge_dct[key]
            for key in merge_dct.keys()
        })
        return rtn_dct
    
    
    def dict_fmerge(self, base_dct, merge_dct, add_keys=True):
        rtn_dct = base_dct.copy()
        if add_keys is False:
            merge_dct = {key: merge_dct[key] for key in set(rtn_dct).intersection(set(merge_dct))}

        if isinstance(merge_dct, dict):
            rtn_dct.update({
                key: self.dict_fmerge(rtn_dct[key], merge_dct[key], add_keys=add_keys)
                if isinstance(rtn_dct.get(key), dict) and isinstance(merge_dct[key], dict)
                else merge_dct[key]
                for key in merge_dct.keys()
            })
        return rtn_dct
    
    @staticmethod
    def dsearch(lod, **kw):
        return filter(lambda i: all((i[k] == v for (k, v) in kw.items())), lod)

    @staticmethod
    def validate_uuid4(uuid_string):
        try:
            uuid.UUID(uuid_string, version=4)
        except ValueError:
            return False
        return True
    
    @staticmethod
    def validate_uuid4_re(uuid_string):
        uuid4hex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
        match = uuid4hex.match(uuid_string)
        return bool(match)
    
    @staticmethod
    def generate_line(num_dash=100, num_greater=0):
        greater_string = '>' * num_greater
        dash_string = '-' * num_dash
        return greater_string + dash_string
    
    
   
    def compare_nested_dicts(self, dict1, dict2, key):
        if key not in dict1 or key not in dict2:
            return None
        
        val1 = dict1[key]
        val2 = dict2[key]
        
        if isinstance(val1, dict) and isinstance(val2, dict):
            # Recursively compare nested dictionaries
            return self.compare_nested_dicts(val1, val2, key)
        else:
            # Compare values for the specified key
            if val1 != val2:
                return False
            else:
                return True





    def convert_to_dict(self, obj):
        if isinstance(obj, dict):
            return {k: self.convert_to_dict(v) for k, v in obj.items()}
        elif is_dataclass(obj):
            # Exclude properties from data class fields
            obj_fields = [f for f in fields(obj) if not isinstance(getattr(obj, f.name), property)]
            return {f.name: self.convert_to_dict(getattr(obj, f.name)) for f in obj_fields}
            #return self.convert_to_dict(asdict(obj))
        elif isinstance(obj, list):
            return [self.convert_to_dict(elem) for elem in obj]
        else:
            return obj



class Range:
    def __init__(self, first=None, last=None):
        self.first = first
        self.last = last
        self.ranges = []

    def add_range(self, start, end):
        if start <= end:
            self.ranges.append(Range(start, end))
        else:
            raise ValueError("Invalid range")

    def get_non_overlapping_ranges(self):
        sorted_ranges = sorted(self.ranges, key=lambda r: r.first)
        non_overlapping_ranges = []
        i = 0
        while i < len(sorted_ranges):
            j = i + 1
            while j < len(sorted_ranges) and sorted_ranges[j].first <= sorted_ranges[i].last:
                if sorted_ranges[j].last > sorted_ranges[i].last:
                    sorted_ranges[i].last = sorted_ranges[j].last
                j += 1
            non_overlapping_ranges.append(Range(sorted_ranges[i].first, sorted_ranges[i].last))
            i = j
        return non_overlapping_ranges

    def __repr__(self):
        return str({"first": self.first, "last": self.last})
    
    def __str__(self):
        return str({"first": self.first, "last": self.last})
    
    
class ErrorApstraBoarding(Exception):
    """
    Error Exception class for handling Apstra Boarding errors
    """
    def __init__(self, message: str, code: http.HTTPStatus = None):
        self.message = message
        self.code = code
        self.codemap = {}
        
        if self.code is not None:
            self.codemap = {k:v for k,v in http.client.responses.items() if k <= self.code} or {self.code: http.client.responses[http.client.INTERNAL_SERVER_ERROR]}
            super().__init__(f"{self.code} {self.codemap[self.code]}: {self.message}")
        else:
            super().__init__(self.message)