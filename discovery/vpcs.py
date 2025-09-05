def list_vpcs(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_vpcs().get("Vpcs", [])