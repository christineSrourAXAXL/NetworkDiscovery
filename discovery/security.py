def list_security_groups(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_security_groups().get("SecurityGroups", [])

def list_nacls(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_network_acls().get("NetworkAcls", [])