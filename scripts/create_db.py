import argparse
import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv


def setup_movies_table():
    parser = argparse.ArgumentParser(
        description="Configurar la tabla de DynamoDB para Movies."
    )
    parser.add_argument(
        "--env",
        choices=["local", "prod"],
        required=True,
        help="Entorno de ejecución: 'local' o 'prod' (AWS)",
    )
    args = parser.parse_args()

    load_dotenv()
    region = os.getenv(
        "AWS_REGION", "us-east-1"
    )

    if args.env == "local":
        endpoint = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:4566")
        print(f"🔧 Configurando entorno LOCAL usando el endpoint: {endpoint}")
        db = boto3.client("dynamodb", endpoint_url=endpoint, region_name=region)
    else:
        print(f"☁️ Configurando entorno de PRODUCCIÓN en AWS (Región: {region})")
        db = boto3.client("dynamodb", region_name=region)

    try:
        print("🚀 Creando tabla 'Movies'...")
        db.create_table(
            TableName="Movies",
            AttributeDefinitions=[
                {"AttributeName": "CenterSlug", "AttributeType": "S"},
                {"AttributeName": "DateTitle", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "CenterSlug", "KeyType": "HASH"},
                {"AttributeName": "DateTitle", "KeyType": "RANGE"},
            ],
            BillingMode="PROVISIONED",
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        print("⏳ Esperando a que la tabla esté activa...")
        waiter = db.get_waiter("table_exists")
        waiter.wait(TableName="Movies")

        print("🕒 Configurando el Time to Live (TTL)...")
        db.update_time_to_live(
            TableName="Movies",
            TimeToLiveSpecification={"Enabled": True, "AttributeName": "ExpiresAt"},
        )

        print(f"✅ Tabla creada con éxito en el entorno [{args.env.upper()}].")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(
                f"⚠️ La tabla 'Movies' ya existe en [{args.env.upper()}]. No se realizaron cambios."
            )
        else:
            print(f"❌ Error inesperado: {e}")


if __name__ == "__main__":
    setup_movies_table()
