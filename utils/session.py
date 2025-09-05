import boto3
import botocore.exceptions

def get_sso_session(accounts: dict):
    """
    Returns a boto3 session authenticated via CLI profile(linked to an sso session NetworkDiscovery)
    """
    profile_name = accounts["sso_profile"]
    region = accounts.get("region", "eu-west-1")

    try:
        session = boto3.Session(profile_name=profile_name, region_name=region)

        # Optionnel : vérifie que la session fonctionne
        sts = session.client("sts")
        result = sts.get_caller_identity()
        return session

        print(result["Arn"])

    except botocore.exceptions.ProfileNotFound:
        raise Exception(f"❌ Profil CLI introuvable : {profile_name}")
    except botocore.exceptions.ClientError as e:
        raise Exception(f"❌ Erreur avec le profil {profile_name} : {e}")

