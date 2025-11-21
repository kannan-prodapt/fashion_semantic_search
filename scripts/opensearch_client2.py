from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

region = "ap-south-1"
service = "es"
host = "vpc-softbank-vector-search-yfbgm75le3fqguq3jntnviw2qu.ap-south-1.es.amazonaws.com"


def get_opensearch_client():
    session = boto3.Session()
    credentials = session.get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        service,
        session_token=credentials.token,
    )

    client = OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30,
        max_retries=3,
        retry_on_timeout=True,
    )
    return client


if __name__ == "__main__":
    client = get_opensearch_client()
    info = client.info()
    print(info)
    health = client.cluster.health()
    print("HEALTH:", health)
