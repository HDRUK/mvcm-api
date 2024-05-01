import json
import os

from google.cloud import pubsub_v1

project_id = os.environ['PROJECT_ID']
topic_id = os.environ['TOPIC_ID']
AUDIT_ENABLED = os.environ.get('AUDIT_ENABLED', False)


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
    