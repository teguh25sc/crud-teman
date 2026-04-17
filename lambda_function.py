import json
import os
import boto3
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)  # atau float(obj)
        return super().default(obj)

        
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE')

if not TABLE_NAME:
    raise Exception("DYNAMODB_TABLE belum diset")

table = dynamodb.Table(TABLE_NAME)


def handler(event, context):
    print(event)
    method = event["httpMethod"]
    path_params = event.get("pathParameters") or {}

    try:
        if method == "GET":
            if "nama" in path_params:
                return read_item(path_params["nama"])
            else:
                return list_items()

        elif method == "POST":
            body = parse_body(event)
            return create_item(body)

        elif method == "PUT":
            if "nama" not in path_params:
                return response(400, {"message": "nama di path wajib"})
            body = parse_body(event)
            return update_item(path_params["nama"], body)

        elif method == "DELETE":
            if "nama" not in path_params:
                return response(400, {"message": "nama di path wajib"})
            return delete_item(path_params["nama"])

        else:
            return response(400, {"message": "Invalid method"})

    except Exception as e:
        return response(500, {"message": str(e)})


# =========================
# CRUD FUNCTIONS
# =========================

def create_item(body):
    nama = body.get("nama")
    umur = body.get("umur")

    if not nama or umur is None:
        return response(400, {"message": "nama dan umur wajib diisi"})

    table.put_item(Item={
        "nama": nama,
        "umur": umur
    })

    return response(201, {"message": "Data berhasil ditambahkan"})


def read_item(nama):
    result = table.get_item(Key={"nama": nama})
    item = result.get("Item")

    if not item:
        return response(404, {"message": "Data tidak ditemukan"})

    return response(200, item)


def update_item(nama, body):
    umur = body.get("umur")

    if umur is None:
        return response(400, {"message": "umur wajib diisi"})

    table.update_item(
        Key={"nama": nama},
        UpdateExpression="SET umur = :u",
        ExpressionAttributeValues={
            ":u": umur
        }
    )

    return response(200, {"message": "Data berhasil diupdate"})


def delete_item(nama):
    table.delete_item(Key={"nama": nama})
    return response(200, {"message": "Data berhasil dihapus"})


def list_items():
    result = table.scan()
    items = result.get("Items", [])
    return response(200, items)


# =========================
# HELPERS
# =========================

def parse_body(event):
    if event.get("body"):
        return json.loads(event["body"])
    return {}


def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }
