import json
import os
import networkx as nx
import plotly.graph_objects as go

# 📂 Load global topology
with open("output/global_topology.json") as f:
    data = json.load(f)

# 📂 Load account name mapping
with open("accounts.json") as f:
    account_list = json.load(f)
account_names = {
    acc["account_id"]: acc.get("account_name", acc["account_id"])
    for acc in account_list
}

# 🎨 Node color map
color_map = {
    "VPC": "lightblue",
    "TGW": "purple",
    "Peering": "gray",
    "Subnet": "lightgreen",
    "ENI": "orange",
}

def get_color(resource_type):
    return color_map.get(resource_type, "lightgray")

def get_name(resource, fallback_id):
    for tag in resource.get("Tags", []):
        if tag.get("Key") == "Name":
            return tag["Value"]
    return fallback_id

# 🧠 Create the graph
G = nx.Graph()

for account_id, regions in data.items():
    account_name = account_names.get(account_id, account_id)
    for region, region_data in regions.items():
        # VPCs
        for vpc in region_data.get("vpcs", []):
            vpc_id = vpc["VpcId"]
            name = get_name(vpc, vpc_id)
            label = f"[VPC] {name}\n{account_name} / {region}"
            G.add_node(vpc_id, type="VPC", label=label)

        # Transit Gateways
        for tgw in region_data.get("transit_gateways", []):
            tgw_id = tgw["TransitGatewayId"]
            name = get_name(tgw, tgw_id)
            label = f"[TGW] {name}\n{account_name} / {region}"
            G.add_node(tgw_id, type="TGW", label=label)

        # TGW Attachments
        for attach in region_data.get("tgw_attachments", []):
            vpc_id = attach.get("ResourceId")
            tgw_id = attach.get("TransitGatewayId")
            if vpc_id and tgw_id:
                G.add_edge(vpc_id, tgw_id)

        # VPC Peering Connections
        for peering in region_data.get("vpc_peering_connections", []):
            req = peering.get("RequesterVpcInfo", {}).get("VpcId")
            acp = peering.get("AccepterVpcInfo", {}).get("VpcId")
            if req and acp:
                G.add_edge(req, acp)

        # Optional: Subnets (displayed as nodes)
        for subnet in region_data.get("subnets", []):
            subnet_id = subnet["SubnetId"]
            name = get_name(subnet, subnet_id)
            label = f"[Subnet] {name}\n{account_name} / {region}"
            G.add_node(subnet_id, type="Subnet", label=label)
            vpc_id = subnet.get("VpcId")
            if vpc_id:
                G.add_edge(subnet_id, vpc_id)

        # Optional: ENIs (Elastic Network Interfaces)
        for eni in region_data.get("enis", []):
            eni_id = eni["NetworkInterfaceId"]
            label = f"[ENI] {eni_id}\n{account_name} / {region}"
            G.add_node(eni_id, type="ENI", label=label)
            subnet_id = eni.get("SubnetId")
            if subnet_id:
                G.add_edge(eni_id, subnet_id)

# 🧪 Summary
print(f"🧠 Total nodes: {len(G.nodes())}")
print(f"🔗 Total edges: {len(G.edges())}")

# 📍 Layout (switch to circle if too few nodes)
layout = nx.spring_layout(G, seed=42) if len(G.nodes()) >= 10 else nx.circular_layout(G)

# 🧭 Build coordinates
edge_x, edge_y = [], []
for edge in G.edges():
    x0, y0 = layout[edge[0]]
    x1, y1 = layout[edge[1]]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]

node_x, node_y, node_text, node_color = [], [], [], []
for node in G.nodes():
    x, y = layout[node]
    node_x.append(x)
    node_y.append(y)
    node_text.append(G.nodes[node].get("label", node))
    node_color.append(get_color(G.nodes[node].get("type", "Unknown")))

# 📈 Build Plotly figure
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=1, color='lightgray'),
    mode='lines'
))

fig.add_trace(go.Scatter(
    x=node_x, y=node_y,
    mode='markers+text',
    text=node_text,
    textposition='top center',
    marker=dict(size=14, color=node_color)
))

fig.update_layout(
    title="🌐 Global AWS Network Topology",
    showlegend=False,
    autosize=True,
    width=1100,
    height=750,
    margin=dict(l=40, r=40, t=60, b=40),
)

# 💾 Save the HTML file
os.makedirs("output", exist_ok=True)
fig.write_html("output/global_topology.html")
print("✅ global_topology.html generated.")
