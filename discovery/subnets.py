def list_subnets(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_subnets().get("Subnets", [])