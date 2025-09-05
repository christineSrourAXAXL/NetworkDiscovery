import os
import json
from datetime import datetime
from utils.session import get_sso_session

from discovery.vpcs import list_vpcs
from discovery.subnets import list_subnets
from discovery.route_tables import list_route_tables
from discovery.gateways import list_internet_gateways, list_nat_gateways, list_transit_gateways
from discovery.endpoints import list_vpc_endpoints
from discovery.enis import list_network_interfaces
from discovery.security import list_security_groups, list_nacls
from discovery.load_balancers import list_load_balancers
from discovery.interconnect import (
    list_transit_gateway_attachments,
    list_vpc_peering_connections,
    list_vpc_endpoint_services
)

def convert(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def save_global_output(data):
    os.makedirs("output", exist_ok=True)
    with open("output/global_topology.json", "w") as f:
        json.dump(data, f, indent=2, default=convert)

def save_account_output(account_id, data):
    os.makedirs("output", exist_ok=True)
    filename = f"output/{account_id}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2, default=convert)

with open("accounts.json") as f:
    accounts = json.load(f)

regions = ["us-east-1", "eu-west-1", "eu-central-1"]
global_data = {}

for acc in accounts:
    account_id = acc["account_id"]
    session = get_sso_session(acc)
    global_data[account_id] = {}

    for reg in regions:
        print(f"🔍 Discovering {account_id} in {reg}")
        region_data = {
            "vpcs": list_vpcs(session, reg),
            "subnets": list_subnets(session, reg),
            "route_tables": list_route_tables(session, reg),
            "internet_gateways": list_internet_gateways(session, reg),
            "nat_gateways": list_nat_gateways(session, reg),
            "transit_gateways": list_transit_gateways(session, reg),
            "vpc_endpoints": list_vpc_endpoints(session, reg),
            "enis": list_network_interfaces(session, reg),
            "security_groups": list_security_groups(session, reg),
            "nacls": list_nacls(session, reg),
            "load_balancers": list_load_balancers(session, reg),
            "tgw_attachments": list_transit_gateway_attachments(session, reg),
            "vpc_peering_connections": list_vpc_peering_connections(session, reg),
            "endpoint_services": list_vpc_endpoint_services(session, reg),
        }

        global_data[account_id][reg] = region_data

    save_account_output(account_id, global_data[account_id])
    print(f" Saved per-account file for {account_id}")

save_global_output(global_data)
print(" Saved global_topology.json")
