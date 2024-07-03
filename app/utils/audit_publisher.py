import json
import os

from google.cloud import pubsub_v1

project_id = os.environ.get('PROJECT_ID', None)
topic_id = os.environ.get('TOPIC_ID', None)
AUDIT_ENABLED = True if os.environ.get('AUDIT_ENABLED', False) in [1, '1'] else False

if AUDIT_ENABLED:
    publisher = pubsub_v1.PublisherClient()
    # The `topic_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/topics/{topic_id}`
    topic_path = publisher.topic_path(project_id, topic_id)


def publish_message(action_type="", action_name="", description=""):
    if AUDIT_ENABLED:
        message_json = {
            "action_type": action_type,
            "action_name": action_name,
            "action_service": "MVCM API",
            "description": description
        }
        encoded_json = json.dumps(message_json).encode("utf-8")
        future = publisher.publish(topic_path, encoded_json)
        return future.result()
