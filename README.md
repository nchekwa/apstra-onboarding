```bash
# python3 onboarding.py  -h
usage: onboarding.py [-h] [-c CONFIG] [-d DEBUG]

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        YAML File (or dir) with configuration
  -d DEBUG, --debug DEBUG
                        Debug Screen Output Level [default: INFO]
```



main features:
- YAML config validate by Draft7 schema
- YAML will not use element IDs but only names/labels
- configuration can be stored in multiple YAML files with anachors references (ie. same vlan for multiple blueprints)
- create resource (asn/ip/vni)
- create blueprints sub elements of Day2 configuration across multiple Bluprints on multiple Apstra Controllers
- create blueprint -> routing-zones
- create blueprint -> virtual-networks (bound to name of phisical swtich (leaf and access) which are translate to redundancy-groups)
- create blueprint -> connectivity-templates (single vlan / multivlan / bgp L3 peering / any othere predefined in jinja template file)
- create blueprint -> nodes (generic or external + links to leaf [Physical  or LAG])
- create blueprint -> nodes (change speed interface if needed)
- assign tags to CT/NODEs/RESOURCEs
- assign node interfaces to assign connectivity-templates to Physical or LAG interface (pointing server interface and then CT provision on Leaf interface side)
- store logging for each run of script in seperate log file


todo:
- create routing-policies
- 'sync=True' option will allow to remove elements on Apstra which are not defined in YAML file
- 'sync=True' will not remove elements from Apstra server (tagged as 'protect' will be keep on apstra side)
- add option -commit for script which will Commit Configuration only if blueprint not repors any errors

