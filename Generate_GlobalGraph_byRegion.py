import json
import os
import networkx as nx
import plotly.graph_objects as go
import hashlib
import matplotlib.colors as mcolors

# Load data
with open("output/global_topology.json") as f:
    data = json.load(f)

with open("accounts.json") as f:
    account_list = json.load(f)

account_names = {
    acc["account_id"]: acc.get("account_name", acc["account_id"])
    for acc in account_list
}

def get_account_color(account_id):
    hex_color = "#" + hashlib.md5(account_id.encode()).hexdigest()[:6]
    return hex_color if hex_color in mcolors.CSS4_COLORS else "#999999"

central_service_colors = {
    "TGW": "purple",
    "TGWAttachment": "orchid",
    "VPCEndpoint": "gold",
    "LoadBalancer": "tomato",
    "Peering": "green",
}

def get_color(node_type, account_id):
    if node_type in central_service_colors:
        return central_service_colors[node_type]
    return get_account_color(account_id)

def get_name(resource, fallback_id):
    for tag in resource.get("Tags", []):
        if tag.get("Key") == "Name":
            return tag["Value"]
    return fallback_id

fig = go.Figure()
region_graphs = {}

for region in sorted(set(r for acc in data.values() for r in acc)):
    G = nx.Graph()

    for account_id, regions in data.items():
        if region not in regions:
            continue
        account_name = account_names.get(account_id, account_id)
        region_data = regions[region]

        added_nodes = set()

        def safe_add_node(node_id, **attrs):
            if "type" not in attrs:
                return
            G.add_node(node_id, **attrs)
            added_nodes.add(node_id)

        def safe_add_edge(src, dst):
            if src in added_nodes and dst in added_nodes:
                G.add_edge(src, dst)

        # VPCs
        for vpc in region_data.get("vpcs", []):
            vpc_id = vpc["VpcId"]
            name = get_name(vpc, vpc_id)
            safe_add_node(vpc_id, type="VPC", label=name, hover=f"[VPC] {name}\n{account_name} / {region}", account=account_id)

        # TGWs
        for tgw in region_data.get("transit_gateways", []):
            tgw_id = tgw["TransitGatewayId"]
            name = get_name(tgw, tgw_id)
            safe_add_node(tgw_id, type="TGW", label=name, hover=f"[TGW] {name}\n{account_name} / {region}", account=account_id)

        # TGW Attachments
        for att in region_data.get("tgw_attachments", []):
            tgw_id = att.get("TransitGatewayId")
            res_id = att.get("ResourceId")
            att_id = f"{res_id}->{tgw_id}"
            safe_add_node(att_id, type="TGWAttachment", label="TGW-Attach", hover=f"[TGWAttachment] {att_id}\n{account_name} / {region}", account=account_id)
            safe_add_edge(att_id, tgw_id)
            safe_add_edge(att_id, res_id)

        # VPC Peering
        for peer in region_data.get("vpc_peering_connections", []):
            peer_id = peer["VpcPeeringConnectionId"]
            req = peer.get("RequesterVpcInfo", {}).get("VpcId")
            acc = peer.get("AccepterVpcInfo", {}).get("VpcId")
            safe_add_node(peer_id, type="Peering", label="Peering", hover=f"[Peering] {peer_id}", account=account_id)
            safe_add_edge(peer_id, req)
            safe_add_edge(peer_id, acc)

        # VPC Endpoints
        for ep in region_data.get("vpc_endpoints", []):
            ep_id = ep["VpcEndpointId"]
            vpc_id = ep["VpcId"]
            name = get_name(ep, ep_id)
            safe_add_node(ep_id, type="VPCEndpoint", label=name, hover=f"[VPCEndpoint] {name}\n{account_name} / {region}", account=account_id)
            safe_add_edge(ep_id, vpc_id)

        # Load Balancers
        for lb in region_data.get("load_balancers", []):
            lb_id = lb["LoadBalancerArn"].split("/")[-2]
            vpc_id = lb.get("VpcId")
            safe_add_node(lb_id, type="LoadBalancer", label="LB", hover=f"[LoadBalancer] {lb_id}\n{account_name} / {region}", account=account_id)
            safe_add_edge(lb_id, vpc_id)

    # Layout with tighter spacing
    layout = nx.spring_layout(G, seed=42, k=0.3, iterations=150)

    edge_x, edge_y = [], []
    for src, dst in G.edges():
        x0, y0 = layout[src]
        x1, y1 = layout[dst]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    node_x, node_y, node_text, node_hover, node_color, node_size = [], [], [], [], [], []
    for node, data in G.nodes(data=True):
        x, y = layout[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(data.get("label", node))
        node_hover.append(data.get("hover", node))
        node_color.append(get_color(data["type"], data["account"]))
        size = 26 if "TGW" in data["type"] else 22 if data["type"] == "VPC" else 14
        node_size.append(size)

    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=1, color='lightgray'), visible=False)
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        hovertext=node_hover,
        textposition='top center',
        marker=dict(size=node_size, color=node_color, line_width=1),
        hoverinfo='text',
        visible=False
    )

    region_graphs[region] = (edge_trace, node_trace)

# Add all region traces
for i, (region, (e_trace, n_trace)) in enumerate(region_graphs.items()):
    e_trace.visible = i == 0
    n_trace.visible = i == 0
    fig.add_trace(e_trace)
    fig.add_trace(n_trace)

# Dropdown filtering
buttons = []
for i, region in enumerate(region_graphs.keys()):
    visibility = [False] * (2 * len(region_graphs))
    visibility[2*i] = True
    visibility[2*i + 1] = True
    buttons.append(dict(label=region, method="update", args=[{"visible": visibility}, {"title": f"Region: {region}"}]))

fig.update_layout(
    title="AWS Global Network Topology",
    showlegend=False,
    width=3000,
    height=2000,
    margin=dict(l=40, r=40, t=60, b=40),
    updatemenus=[{
        "buttons": buttons,
        "direction": "down",
        "pad": {"r": 10, "t": 10},
        "showactive": True,
        "x": 0.01,
        "xanchor": "left",
        "y": 1.1,
        "yanchor": "top"
    }]
)

os.makedirs("output", exist_ok=True)
fig.write_html("output/global_network_topology_byRegion.html")
print("✅ Graph saved to: output/global_network_topology_byRegion.html")

