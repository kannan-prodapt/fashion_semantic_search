import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

REGION = "ap-south-1"
HOST = "vpc-softbank-vector-search-yfbgm75le3fqguq3jntnviw2qu.ap-south-1.es.amazonaws.com"


def get_opensearch_client():
    # Get temporary credentials from the instance role (opensearch-role)
    session = boto3.Session()
    credentials = session.get_credentials()
    auth = AWSV4SignerAuth(credentials, REGION)

    client = OpenSearch(
        hosts=[{"host": HOST, "port": 443}],
        http_auth=auth,  # ✅ SIGV4, not ("admin","pwd")
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )
    return client


if __name__ == "__main__":
    client = get_opensearch_client()
    print(client.info())
