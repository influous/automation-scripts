import boto3
import schedule
from datetime import datetime

ec2_client = boto3.client("ec2", region_name="eu-central-1")
ec2_resource = boto3.resource("ec2", region_name="eu-central-1")


def check_instance_status():
    instance_statuses = ec2_client.describe_instance_status(
        IncludeAllInstances=True)
    for instance_status in instance_statuses["InstanceStatuses"]:
        ins_status = instance_status["InstanceStatus"]["Status"]
        sys_status = instance_status["SystemStatus"]["Status"]
        state = instance_status["InstanceState"]["Name"]
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] Instance {instance_status['InstanceId']}: State is {state} with status {ins_status} and system status is {sys_status}."
        )


schedule.every(10).seconds.do(check_instance_status)

while True:
    schedule.run_pending()
