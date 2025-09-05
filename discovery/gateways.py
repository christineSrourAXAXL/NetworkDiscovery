def list_internet_gateways(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_internet_gateways().get("InternetGateways", [])

def list_nat_gateways(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_nat_gateways().get("NatGateways", [])

def list_transit_gateways(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_transit_gateways().get("TransitGateways", [])
