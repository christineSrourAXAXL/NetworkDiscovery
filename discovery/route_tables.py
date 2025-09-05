def list_route_tables(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_route_tables().get("RouteTables", [])