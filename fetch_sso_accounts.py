import boto3
import json

SSO_PROFILE = "Security"  # votre profil configuré SSO
REGION = "eu-west-1"
ROLE_NAME = "plt-security-ro"

# Créer une session boto3 avec le profil SSO
session = boto3.Session(profile_name=SSO_PROFILE)

# Créer le client SSO via cette session
sso_client = session.client("sso", region_name=REGION)

def get_accounts():
    accounts = []
    next_token = None
    while True:
        kwargs = {"maxResults": 50}
        if next_token:
            kwargs["nextToken"] = next_token
        resp = sso_client.list_accounts(**kwargs)
        for acct in resp["accountList"]:
            accounts.append({
                "account_id": acct["accountId"]
            })
        next_token = resp.get("nextToken")
        if not next_token:
            break
    return accounts

accounts = get_accounts()

# Ajouter le profil SSO pour chaque compte
for acc in accounts:
    acc["sso_profile"] = f"{ROLE_NAME}-{acc['account_id']}"
    acc["role_name"] = ROLE_NAME

# Enregistrer dans un fichier JSON
with open("accounts.json", "w") as f:
    json.dump(accounts, f, indent=2)
