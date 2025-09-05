def list_transit_gateway_attachments(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_transit_gateway_attachments().get("TransitGatewayAttachments", [])

def list_vpc_peering_connections(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_vpc_peering_connections().get("VpcPeeringConnections", [])

def list_vpc_endpoint_services(session, region):
    ec2 = session.client("ec2", region_name=region)
    return ec2.describe_vpc_endpoint_service_configurations().get("ServiceConfigurations", [])
