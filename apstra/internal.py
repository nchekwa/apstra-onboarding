#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import sys
sys.dont_write_bytecode = True

import logging
logger = logging.getLogger(__name__)

import uuid
import re

from time import sleep
from typing import NamedTuple
from dataclasses import is_dataclass, asdict


class Internal:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.parameters = main_class.parameters
        self.handlers = main_class.handlers

            
    def dict_fmerge(self, base_dct, merge_dct, add_keys=True):
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
    
    @staticmethod
    def copy_dataclass(source, destination):
        for key, value in vars(source).items():
            setattr(destination, key, value)

    @staticmethod
    def redacted(d):
        if d is None or d == "":
            return d

        if isinstance(d, str):
            return d
        h = d.copy()
        for sensitive in ["password", "token", "AuthToken"]:
            if sensitive in d:
                h[sensitive] = "<REDACTED>"
        return h


    def convert_to_dict(self, obj):
        if isinstance(obj, dict):
            return {k: self.convert_to_dict(v) for k, v in obj.items()}
        elif is_dataclass(obj):
            return self.convert_to_dict(asdict(obj))
        elif isinstance(obj, list):
            return [self.convert_to_dict(elem) for elem in obj]
        else:
            return obj

class Colors(NamedTuple):
    RED: str
    GREEN: str
    GREEN0: str
    YELLOW: str
    BLUE: str
    RESET: str

class Color:
    def __init__(self):
        self.colors = Colors(
            RED='\033[1;31m',
            GREEN='\033[1;32m',
            GREEN0='\033[0;32m',
            YELLOW='\033[1;33m',
            BLUE='\033[1;34m',
            RESET='\033[0m'
        )

    def get(self, name: str) -> str:
        return getattr(self.colors, name)