def list_vpc_endpoints(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_vpc_endpoints().get("VpcEndpoints", [])