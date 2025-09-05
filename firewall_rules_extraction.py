import boto3
import json
import os
from datetime import datetime

def default_serializer(o):
    if isinstance(o, (datetime,)):
        return o.isoformat()
    return o

def lowercase_keys(obj):
    if isinstance(obj, dict):
        return {k.lower(): lowercase_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [lowercase_keys(i) for i in obj]
    else:
        return obj

def discover_network_firewalls(session, region):
    """
    Returns a list of dicts, each containing:
      - firewall_name
      - vpc_id
      - subnet_mappings
      - firewall_policy (metadata + document)
      - rule_group_definitions { arn: full_rule_group_body, … }
    All keys are lowercase.
    """
    client = session.client("network-firewall", region_name=region)
    out = []

    # 1) list all firewalls
    for page in client.get_paginator("list_firewalls").paginate():
        for fw in page["Firewalls"]:
            name       = fw["FirewallName"]
            detail     = client.describe_firewall(FirewallName=name)["Firewall"]
            policy_arn = detail["FirewallPolicyArn"]

            # 2) describe the policy
            resp = client.describe_firewall_policy(FirewallPolicyArn=policy_arn)
            policy_doc  = resp.get("FirewallPolicy", {})
            policy_meta = resp.get("FirewallPolicyResponse", {})

            # 3) gather all rule-group ARNs
            stateless_refs = policy_doc.get("StatelessRuleGroupReferences", [])
            stateful_refs  = policy_doc.get("StatefulRuleGroupReferences", [])

            all_refs = stateless_refs + stateful_refs
            rule_defs = {}

            # 4) for each reference, describe_rule_group
            for ref in all_refs:
                arn = ref.get("RuleGroupArn") or ref.get("ResourceArn")
                if not arn or arn in rule_defs:
                    continue
                rg_resp = client.describe_rule_group(RuleGroupArn=arn)
                # both response keys have definitions; merge them
                rg_meta = rg_resp.get("RuleGroupResponse", {})
                rg_body = rg_resp.get("RuleGroup", {})
                rule_defs[arn] = {
                    "metadata": rg_meta,
                    "definition": rg_body
                }

            out.append(lowercase_keys({
                "firewall_name": name,
                "vpc_id": detail["VpcId"],
                "subnet_mappings": detail.get("SubnetMappings", []),
                "firewall_policy": {
                    "metadata": policy_meta,
                    "document": policy_doc
                },
                "rule_group_definitions": rule_defs
            }))

    return out

def main():
    # Set your profile name
    profile_name = "Network-LZA"
    region = "eu-west-1"  
    session = boto3.Session(profile_name=profile_name)
    result = discover_network_firewalls(session, region)

    with open("output/firewall_rules_info.json", "w") as f:
        json.dump(result, f, default=default_serializer, indent=2)
    print(f"Firewall rules info saved to firewall_rules_info.json")

if __name__ == "__main__":
    main()
