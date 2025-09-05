def list_load_balancers(session, region):
    elb = session.client("elbv2", region_name=region)
    return elb.describe_load_balancers().get("LoadBalancers", [])