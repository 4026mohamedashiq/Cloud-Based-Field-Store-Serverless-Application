"""
FC Cloud Manager - Serverless Event-Driven Sports Analytics Backend
AWS Lambda API Handler
Author: S. Mohamed Ashiq
Club: FC Cloud Rovers
"""

import json
import os
import boto3
from decimal import Decimal
from botocore.exceptions import ClientError

# Configuration & AWS Resource Initialization
AWS_REGION = os.environ.get('AWS_REGION', 'ap-southeast-2')
PLAYERS_TABLE_NAME = os.environ.get('PLAYERS_TABLE', 'players')
FIXTURES_TABLE_NAME = os.environ.get('FIXTURES_TABLE', 'FC_fixtures')
STATS_TABLE_NAME = os.environ.get('STATS_TABLE', 'team_stats')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
players_table = dynamodb.Table(PLAYERS_TABLE_NAME)
fixtures_table = dynamodb.Table(FIXTURES_TABLE_NAME)

sns_client = boto3.client('sns', region_name=AWS_REGION) if SNS_TOPIC_ARN else None

# Helper to fix JSON serialization with DynamoDB Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

# Standard CORS headers for web browser communication
CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Requested-With",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
}

def build_response(status_code, body):
    """Builds a standardized API Gateway HTTP response."""
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, cls=DecimalEncoder) if not isinstance(body, str) else body
    }

def normalize_path(raw_path):
    """Cleans duplicate slashes and trailing slashes for reliable routing."""
    if not raw_path:
        return "/"
    # Remove redundant slashes e.g. //players -> /players
    while "//" in raw_path:
        raw_path = raw_path.replace("//", "/")
    # Strip trailing slash if longer than 1 character
    if len(raw_path) > 1 and raw_path.endswith("/"):
        raw_path = raw_path[:-1]
    return raw_path

def lambda_handler(event, context):
    """
    Main Lambda entry point. Supports:
    1. API Gateway HTTP API (Payload v2.0)
    2. API Gateway REST API (Payload v1.0)
    3. DynamoDB Streams triggers (for real-time team stats calculations)
    """
    # -------------------------------------------------------------
    # 1. Check if invoked by DynamoDB Streams
    # -------------------------------------------------------------
    if "Records" in event and len(event["Records"]) > 0:
        first_record = event["Records"][0]
        if first_record.get("eventSource") == "aws:dynamodb":
            return handle_dynamodb_stream(event)

    # -------------------------------------------------------------
    # 2. Extract HTTP Method and Path (v1.0 & v2.0 compatible)
    # -------------------------------------------------------------
    request_context = event.get('requestContext', {})
    http_context = request_context.get('http', {})

    http_method = (
        http_context.get('method') or
        event.get('httpMethod') or
        ''
    ).upper()

    raw_path = (
        http_context.get('path') or
        event.get('rawPath') or
        event.get('path') or
        '/'
    )
    path = normalize_path(raw_path)

    # Handle CORS Preflight request
    if http_method == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": ""
        }

    # Parse Request Body
    body = {}
    raw_body = event.get('body')
    if raw_body:
        try:
            body = json.loads(raw_body)
        except Exception:
            body = {}

    query_params = event.get('queryStringParameters') or {}

    try:
        # ---------------------------------------------------------
        # ROUTE: Health / Root
        # ---------------------------------------------------------
        if path in ["", "/"]:
            return build_response(200, {
                "service": "FC Cloud Manager API",
                "status": "online",
                "club": "FC Cloud Rovers",
                "manager": "S.Mohamed Ashiq"
            })

        # ---------------------------------------------------------
        # ROUTE: /players (Squad Roster CRUD)
        # ---------------------------------------------------------
        if path == "/players":
            if http_method == 'GET':
                response = players_table.scan()
                players = response.get('Items', [])
                return build_response(200, players)

            elif http_method == 'POST':
                if not body.get('playerId') or not body.get('name'):
                    return build_response(400, {"error": "Missing required fields: playerId and name are required."})

                # Sanitize player record
                player_item = {
                    "playerId": str(body['playerId']),
                    "name": str(body['name']),
                    "position": str(body.get('position', 'Forward')),
                    "jerseyNumber": int(body.get('jerseyNumber', 0)),
                    "fitness": str(body.get('fitness', '100%'))
                }

                players_table.put_item(Item=player_item)

                # Optional: Publish SNS notification for injury or signing
                if sns_client and SNS_TOPIC_ARN:
                    try:
                        sns_client.publish(
                            TopicArn=SNS_TOPIC_ARN,
                            Subject=f"Squad Update: {player_item['name']}",
                            Message=f"Player {player_item['name']} ({player_item['position']}, #{player_item['jerseyNumber']}) registered/updated. Fitness: {player_item['fitness']}"
                        )
                    except Exception as sns_err:
                        print(f"SNS publish failed (non-critical): {sns_err}")

                return build_response(201, {
                    "message": "Player permanently saved to DynamoDB!",
                    "item": player_item
                })

            elif http_method == 'DELETE':
                player_id = query_params.get('playerId') or body.get('playerId')
                if not player_id:
                    return build_response(400, {"error": "playerId parameter is required for deletion."})

                players_table.delete_item(Key={"playerId": str(player_id)})
                return build_response(200, {"message": f"Player {player_id} deleted successfully."})

        # ---------------------------------------------------------
        # ROUTE: /fixtures (Match Schedule CRUD)
        # ---------------------------------------------------------
        elif path == "/fixtures":
            if http_method == 'GET':
                response = fixtures_table.scan()
                fixtures = response.get('Items', [])
                return build_response(200, fixtures)

            elif http_method == 'POST':
                if not body.get('opponent') or not body.get('date'):
                    return build_response(400, {"error": "Missing required fields: opponent and date."})

                fixture_item = {
                    "fixtureId": str(body.get('fixtureId', f"FIX_{body.get('date')}_{body.get('opponent')}")),
                    "date": str(body['date']),
                    "venue": str(body.get('venue', 'Home')),
                    "opponent": str(body['opponent']),
                    "competition": str(body.get('competition', 'Premier League')),
                    "result": str(body.get('result', 'Upcoming'))
                }

                fixtures_table.put_item(Item=fixture_item)
                return build_response(201, {
                    "message": "Fixture permanently saved!",
                    "item": fixture_item
                })

        # ---------------------------------------------------------
        # ROUTE: /stats (Team & Squad Analytics)
        # ---------------------------------------------------------
        elif path == "/stats":
            if http_method == 'GET':
                # Compute live stats from DynamoDB players table
                players_res = players_table.scan()
                items = players_res.get('Items', [])

                squad_size = len(items)
                injuries = [p for p in items if 'injury' in str(p.get('fitness', '')).lower() or 'knock' in str(p.get('fitness', '')).lower()]
                positions = {}
                for p in items:
                    pos = p.get('position', 'Unknown')
                    positions[pos] = positions.get(pos, 0) + 1

                analytics = {
                    "squadSize": squad_size,
                    "injuredCount": len(injuries),
                    "injuredPlayers": [p.get('name') for p in injuries],
                    "positionsBreakdown": positions,
                    "nextFixture": "vs Real Madrid (A)",
                    "topScorer": "Cristiano (25)",
                    "winRate": "85.0%"
                }
                return build_response(200, analytics)

        # ---------------------------------------------------------
        # ROUTE: /login (Simple authentication helper)
        # ---------------------------------------------------------
        elif path == "/login":
            if http_method == 'POST':
                username = body.get('username')
                password = body.get('password')
                if username == "manager" and password == "admin123":
                    return build_response(200, {
                        "authenticated": True,
                        "token": "fc-session-token-valid",
                        "manager": "S.Mohamed Ashiq",
                        "club": "FC Cloud Rovers"
                    })
                return build_response(401, {"authenticated": False, "error": "Invalid manager credentials."})

        # Fallback for unrecognized routes
        return build_response(404, {
            "message": f"Route Not Found: [{http_method}] {path}",
            "availableRoutes": [
                "GET /players",
                "POST /players",
                "DELETE /players?playerId=<id>",
                "GET /fixtures",
                "POST /fixtures",
                "GET /stats",
                "POST /login"
            ]
        })

    except ClientError as ce:
        print(f"DynamoDB ClientError: {ce.response['Error']['Message']}")
        return build_response(500, {"error": "Database error", "details": ce.response['Error']['Message']})
    except Exception as e:
        print(f"Server Exception: {str(e)}")
        return build_response(500, {"error": str(e)})

def handle_dynamodb_stream(event):
    """
    Event-driven processor triggered by DynamoDB Streams.
    Processes newly inserted or modified records to calculate analytics and trigger alerts.
    """
    print(f"Processing {len(event.get('Records', []))} DynamoDB Stream records...")
    
    for record in event.get('Records', []):
        event_name = record.get('eventName')  # INSERT, MODIFY, REMOVE
        print(f"DynamoDB Stream Event: {event_name}")
        
        # Deserialize DynamoDB item if present
        new_image = record.get('dynamodb', {}).get('NewImage', {})
        if new_image:
            player_name = new_image.get('name', {}).get('S', 'Unknown')
            fitness = new_image.get('fitness', {}).get('S', '100%')
            position = new_image.get('position', {}).get('S', 'Unknown')
            
            # Check for injuries and alert via SNS if configured
            if any(term in fitness.lower() for term in ['injury', 'knock', 'hamstring', 'ankle']):
                alert_msg = f"MEDICAL ROOM ALERT: {player_name} ({position}) has reported: {fitness}."
                print(f"[ALERT] {alert_msg}")
                if sns_client and SNS_TOPIC_ARN:
                    try:
                        sns_client.publish(
                            TopicArn=SNS_TOPIC_ARN,
                            Subject="FC Cloud Medical Room Alert",
                            Message=alert_msg
                        )
                    except Exception as err:
                        print(f"Failed to publish SNS alert: {err}")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "DynamoDB Stream batch processed successfully."})
    }

# -------------------------------------------------------------
# Local Development Server (Optional)
# Allows running 'python lambda_function.py' for local testing
# -------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class LocalHandler(BaseHTTPRequestHandler):
        def do_OPTIONS(self):
            self.send_response(200)
            for k, v in CORS_HEADERS.items():
                self.send_header(k, v)
            self.end_headers()

        def do_GET(self):
            self.handle_req('GET')

        def do_POST(self):
            self.handle_req('POST')

        def do_DELETE(self):
            self.handle_req('DELETE')

        def handle_req(self, method):
            content_len = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_len).decode('utf-8') if content_len > 0 else ""

            event = {
                "requestContext": {
                    "http": {
                        "method": method,
                        "path": self.path.split('?')[0]
                    }
                },
                "rawPath": self.path.split('?')[0],
                "queryStringParameters": dict(qc.split('=') for qc in self.path.split('?')[1].split('&')) if '?' in self.path else {},
                "body": post_body
            }

            resp = lambda_handler(event, None)
            self.send_response(resp['statusCode'])
            for k, v in resp.get('headers', {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.get('body', '').encode('utf-8'))

    port = 8000
    print(f"Starting local mock server at http://127.0.0.1:{port} ...")
    print("Press Ctrl+C to stop.")
    server = HTTPServer(('127.0.0.1', port), LocalHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)

