#!/usr/bin/env -S uv run
#MISE description="Setup db"

import os
import subprocess
import time

import boto3
from botocore.exceptions import ClientError

# Infraestructura
subprocess.run(["docker", "compose", "down", "-v"], check=True)
subprocess.run(["docker", "compose", "up", "-d"], check=True)
time.sleep(1)


def setup_movies_table():
    region = os.getenv("AWS_REGION", "us-east-1")
    endpoint = os.getenv("DYNAMODB_ENDPOINT")

    if endpoint:
        print(f"🔧 Configurando entorno LOCAL usando el endpoint: {endpoint}")
        db = boto3.client(
            "dynamodb",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
        env = "local"
    else:
        print(f"☁️ Configurando entorno de PRODUCCIÓN en AWS (Región: {region})")
        db = boto3.client("dynamodb", region_name=region)
        env = "prod"

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

        print(f"✅ Tabla creada con éxito en el entorno {env}.")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"⚠️ La tabla 'Movies' ya existe en {env}. No se realizaron cambios.")
        else:
            print(f"❌ Error inesperado: {e}")


if __name__ == "__main__":
    setup_movies_table()
