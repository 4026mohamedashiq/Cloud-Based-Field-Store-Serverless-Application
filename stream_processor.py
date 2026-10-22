"""
FC Cloud Manager - DynamoDB Streams Processor (Event-Driven Analytics)
Author: S. Mohamed Ashiq
Club: FC Cloud Rovers

Triggered automatically whenever items are inserted, updated, or removed
in the DynamoDB 'players' table.
"""

import json
import os
import boto3
from decimal import Decimal

AWS_REGION = os.environ.get('AWS_REGION', 'ap-southeast-2')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
STATS_TABLE_NAME = os.environ.get('STATS_TABLE', 'team_stats')

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
sns_client = boto3.client('sns', region_name=AWS_REGION) if SNS_TOPIC_ARN else None

def lambda_handler(event, context):
    print(f"Received DynamoDB Stream event with {len(event.get('Records', []))} records.")
    
    for record in event.get('Records', []):
        event_name = record.get('eventName')  # INSERT, MODIFY, REMOVE
        print(f"Event: {event_name} | EventID: {record.get('eventID')}")

        if event_name in ['INSERT', 'MODIFY']:
            new_image = record.get('dynamodb', {}).get('NewImage', {})
            player_id = new_image.get('playerId', {}).get('S', 'N/A')
            name = new_image.get('name', {}).get('S', 'Unknown')
            position = new_image.get('position', {}).get('S', 'Unknown')
            jersey = new_image.get('jerseyNumber', {}).get('N', '0')
            fitness = new_image.get('fitness', {}).get('S', '100%')

            print(f"Processed Player: {name} (ID: {player_id}, Pos: {position}, #{jersey}, Fitness: {fitness})")

            # Detect injuries or health concerns and trigger SNS alert
            is_injured = any(w in fitness.lower() for w in ['injury', 'knock', 'strain', 'sprain', 'hamstring'])
            if is_injured and SNS_TOPIC_ARN and sns_client:
                subject = f"🚨 Medical Room Alert: {name}"
                message = (
                    f"Player Fitness Notification:\n"
                    f"- Player: {name} (#{jersey})\n"
                    f"- Position: {position}\n"
                    f"- Status: {fitness}\n\n"
                    f"Please review squad availability in the FC Cloud Manager Dugout."
                )
                try:
                    sns_client.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Subject=subject,
                        Message=message
                    )
                    print(f"Sent SNS alert for injured player: {name}")
                except Exception as e:
                    print(f"Error publishing SNS notification: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Successfully processed DynamoDB Stream events."})
    }

