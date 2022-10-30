import requests
import smtplib
import os
import paramiko
import linode_api4
import time
from datetime import datetime
import schedule

LINODE_ACCOUNT_ID = os.environ.get('LINODE_ACCOUNT_ID')
LINODE_SERVER_IP = os.environ.get('LINODE_SERVER_IP')
LINODE_TOKEN = os.environ.get('LINODE_TOKEN')
EMAIL_SMTP_SERVER = os.environ.get('EMAIL_SMTP_SERVER')
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
SSH_KEY_PATH = '/Users/tobias/.ssh/linode.pem'
SSH_USERNAME = 'root'
CONTAINER_ID = 'aa1e79b02592'
CONTAINER_PORT = 8080


def get_current_time():
    return str(f"[{datetime.now().strftime('%H:%M:%S')}]")


def restart_server_and_container():
    client = linode_api4.LinodeClient(LINODE_TOKEN)
    nginx_server = client.load(linode_api4.Instance, LINODE_ACCOUNT_ID)
    nginx_server.reboot()
    print(f"{get_current_time()} The Linode server is rebooting now...")

    while True:
        nginx_server = client.load(linode_api4.Instance, LINODE_ACCOUNT_ID)
        if nginx_server.status == 'running':
            time.sleep(10)
            restart_container()
            title, message = 'Site Up', 'Site is available again.'
            send_notification(title, message)
            break


def send_notification(email_title, email_msg):
    print(f"{get_current_time()} Sending an email...")
    with smtplib.SMTP(EMAIL_SMTP_SERVER, 587) as smtp:
        smtp.starttls()
        smtp.ehlo()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        msg = f"Subject: {email_title}\n{email_msg}"
        smtp.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, msg)


def restart_container():
    print(f"{get_current_time()} Restarting the container...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(LINODE_SERVER_IP,
                key_filename=SSH_KEY_PATH, username=SSH_USERNAME)
    stdin, stdout, stderr = ssh.exec_command(f"docker restart {CONTAINER_ID}")
    cleaned_output = str(stdout.readlines())
    print(
        f"{get_current_time()} Container '{cleaned_output[2:-4]}' restarted.")
    ssh.close()


def monitor_application():
    try:
        response = requests.get(
            f"http://{LINODE_SERVER_IP.replace('.', '-')}.ip.linodeusercontent.com:{CONTAINER_PORT}/")

        if response.status_code == 200:
            print(f"{get_current_time()} Application is up.")
        else:
            print(f"{get_current_time()} Applicaton down. Action is required.")
            title, message = 'Site Down', f"Application returned {response.status_code}. Fix needed."
            send_notification(title, message)
            restart_container()

    except Exception as e:
        title, message = 'Site Down', 'Application unreachable.'
        print(f"{get_current_time()} Connection error: {e}")
        print(f"{get_current_time()} {message}")
        send_notification(title, message)
        restart_server_and_container()


schedule.every().minute.do(monitor_application)

while True:
    schedule.run_pending()
