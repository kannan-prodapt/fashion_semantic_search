# app/opensearch_client.py
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

REGION = "ap-south-1"
SERVICE = "es"
HOST = "vpc-softbank-vector-search-yfbgm75le3fqguq3jntnviw2qu.ap-south-1.es.amazonaws.com"


def get_opensearch_client():
    """
    Uses the EC2 instance IAM role (opensearch-role) with SigV4 auth
    to connect to your VPC OpenSearch domain.
    """
    session = boto3.Session()
    credentials = session.get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        REGION,
        SERVICE,
        session_token=credentials.token,
    )

    client = OpenSearch(
        hosts=[{"host": HOST, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30,
        max_retries=3,
        retry_on_timeout=True,
    )
    return client
