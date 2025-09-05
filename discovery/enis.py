def list_network_interfaces(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_network_interfaces().get("NetworkInterfaces", [])
