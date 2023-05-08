#!/usr/bin/python3
import sys
sys.dont_write_bytecode = True
import os, warnings
import pandas as pd
import yaml
import argparse
from typing import List, Dict
import numpy as np

# Filter out the specific warning message
warnings.filterwarnings("ignore", message="Data Validation extension is not supported and will be removed", module="openpyxl.worksheet._reader")

def get_as_list(string: str) -> List[str]:
    """Splits a string by commas and returns a list of stripped values."""
    l = []
    if ',' in string:
        l = [value.strip() for value in string.split(',')]
    else:
        l.append(string)
    return l


def sort_fields(data: dict, config_section_name: str = "global") -> Dict:
    field_names_dict = {
        "virtual-networks": ['name', 'routing-zone', 'vlan_id', 'vn_id', 'ipv4_enabled', 'ipv4_subnet', 'virtual_gateway_ipv4'],
        "routing-zones": ['name', 'vlan_id', 'ipv4_subnet'],
        "global": ['aos', 'resource', 'blueprints'],
    }
    field_names = field_names_dict.get(config_section_name, ['name'])

    sorted_items = sorted(data.items(), key=lambda x: field_names.index(x[0]) if x[0] in field_names else len(field_names))
    sorted_dict = {k: v for k, v in sorted_items}
    return sorted_dict

if __name__ == "__main__":
    # Set up command line argument parser
    parser = argparse.ArgumentParser(description='Convert Excel file to YAML format.')
    parser.add_argument('-f', '--file', metavar='filename', required=True, help='the name of the Excel file to convert')
    args = parser.parse_args()

    # Load Excel file
    try:
        excel_file = pd.ExcelFile(args.file)
    except Exception as e:
        print(f"ERROR: File '{args.file}' Not Found")
        exit(1)

    # Prepere data YAML
    data = dict()
    data['blueprints'] = dict()
    data['resource'] = dict()
    data['resource'] = {"ip-pools": list(), "vni-pools": list(), "asn-pools": list()}

    # Cover 'blueprints' spreadsheet
    blueprints_spreadsheet = excel_file.parse('blueprints').to_dict(orient='records')
    bp = dict()
    for row in blueprints_spreadsheet:
        data['blueprints'][row['blueprint']] = dict()
        bp.setdefault(row['ApstraName'], list()).append(row['blueprint'])

    # Cover 'aos' spreadsheet
    aos_spreadsheet = excel_file.parse('aos').to_dict(orient='records')
    for row in aos_spreadsheet:
            name = row['name']
            data.setdefault('aos', {})[name] = dict()
            for key, value in row.items():
                if value is not None:
                    data['aos'][name][key] = value
            del(data['aos'][name]['name'])
            
            if bp.get(name):
                data['aos'][name]['blueprints'] = bp[name]

    # Cover 'resource' spreadsheets
    sheets = ['ip-pools', 'vni-pools', 'asn-pools']
    for config_section in sheets:
        sheet = excel_file.parse(config_section).to_dict(orient='records')
        for row in sheet:
            if config_section == "ip-pools" and row.get('subnets'):
                row['subnets'] = get_as_list(row['subnets'])
            if (config_section == "vni-pools" or config_section == "asn-pools") and row.get('ranges'):
                row['ranges'] = get_as_list(row['ranges'])
                
            data['resource'][config_section].append(row)

    # Cover othere spreadsheet
    sheets = ['routing-zones', 'virtual-networks']
    for config_section in sheets:
        sheet = excel_file.parse(config_section).to_dict(orient='records')
        for row in sheet:
            bp_names = get_as_list(row['blueprint'])
            del(row['blueprint'])
            
            for bp_name in bp_names:
                data['blueprints'][bp_name].setdefault(config_section, list()) 
                
                config_element = dict()
                for key,value in row.items():
                    if isinstance(value, float) and np.isnan(value):
                        continue
                    
                    if isinstance(value, str) and value is None:
                        continue
                    
                    if config_section == "routing-zones" and (key == "dhcp_servers" or key == "leaf_loopback_ip_pools"):
                        config_element[key] = get_as_list(value)
                        continue
                    
                    if config_section == "virtual-networks" and key == "bound_to":
                        devices = get_as_list(value)
                        for device in devices:
                            config_element.setdefault(key, list()).append({"system": device})
                        continue
                    
                    config_element[key] = value
                
                config_element_sorted = sort_fields(config_element, config_section)
                data['blueprints'][bp_name][config_section].append(config_element_sorted)



    # Convert dictionary to YAML and write to file
    base_name, extension = os.path.splitext(args.file)
    yaml_file_name = base_name + ".yaml"
    with open(yaml_file_name, 'w') as f:
        yaml.dump(sort_fields(data), f, sort_keys=False)
        
    print(f"Done! -> {yaml_file_name}")
        
        
        