#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import sys
sys.dont_write_bytecode = True

import logging
logger = logging.getLogger(__name__)

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Resources:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters

        from apstra.resources_ipv4 import ResourcesIPv4Pool
        self.ipv4_pools = ResourcesIPv4Pool(self.apstra)
        from apstra.resources_vni import ResourcesVniPool
        self.vni_pools = ResourcesVniPool(self.apstra)
        from apstra.resources_asn import ResourcesAsnPool
        self.asn_pools = ResourcesAsnPool(self.apstra)


    def apply_resource_groups(self, bp_id: str, resource_type: str, group_name: str, pool_ids: list):
        uri = f"/api/blueprints/{bp_id}/resource_groups/{resource_type}/{group_name}"
        data = {"pool_ids": pool_ids}

        rg = self.apstra.rest.put_json_response(uri, data=data)
        return rg




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

    def get_non_overlapping_ranges(self) -> list:
        sorted_ranges = sorted(self.ranges, key=lambda r: r.first)
        non_overlapping_ranges = []
        i = 0
        while i < len(sorted_ranges):
            j = i + 1
            while j < len(sorted_ranges) and sorted_ranges[j].first <= sorted_ranges[i].last:
                if sorted_ranges[j].last > sorted_ranges[i].last:
                    sorted_ranges[i].last = sorted_ranges[j].last
                j += 1
            r = {"first": sorted_ranges[i].first, "last":sorted_ranges[i].last}
            non_overlapping_ranges.append(r)
            i = j
        return non_overlapping_ranges

    def __repr__(self):
        return str({"first": self.first, "last": self.last})
    
    def __str__(self):
        return str({"first": self.first, "last": self.last})