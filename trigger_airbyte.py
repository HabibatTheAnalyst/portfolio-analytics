import os
import time

import requests

api_url = "https://api.airbyte.com/v1"
poll_seconds = 10
max_wait_seconds = 30 * 60

def check(response, action):
    # raise a clear error if Airbyte rejects the request
    if not response.ok:
        raise RuntimeError(f"{action} failed ({response.status_code}): {response.text}")
    return response.json()

def get_token():
    response = requests.post(
        f"{api_url}/applications/token",
        json={
            "client_id": os.environ["AIRBYTE_CLIENT_ID"],
            "client_secret": os.environ["AIRBYTE_CLIENT_SECRET"],
        },
        timeout=30,
    )
    return check(response, "Getting access token")["access_token"]

def get_connection_ids():
    # comma-separated list from the environment, e.g. "id1,id2"
    ids = [
        c.strip() for c in os.environ["AIRBYTE_CONNECTION_IDS"].split(",") if c.strip()
    ]
    if not ids:
        raise RuntimeError("AIRBYTE_CONNECTION_IDS is empty")
    return ids

def start_sync(token, connection_id):
    response = requests.post(
        f"{api_url}/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json={"connectionId": connection_id, "jobType": "sync"},
        timeout=30,
    )
    return check(response, "Starting sync")["jobId"]

def start_all_syncs(token, connection_ids):
    # start every sync first, so they run in parallel
    jobs = {}
    for connection_id in connection_ids:
        jobs[connection_id] = start_sync(token, connection_id)
        print(f"Started job {jobs[connection_id]} for connection {connection_id}")
    return jobs

def wait_for_job(token, job_id):
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        response = requests.get(
            f"{api_url}/jobs/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        job = check(response, "Checking job status")
        status = str(job["status"]).lower()
        print(f"Job {job_id}: {status}")

        if status == "succeeded":
            return job
        if status in ("failed", "cancelled", "incomplete"):
            raise RuntimeError(f"Airbyte job {job_id} ended with status '{status}'")
        time.sleep(poll_seconds)

    raise TimeoutError(f"Airbyte job {job_id} did not finish within {max_wait_seconds}s")

def wait_for_all(token, jobs):
    for job_id in jobs.values():
        wait_for_job(token, job_id)
    print(f"All {len(jobs)} Airbyte sync(s) finished")

def main():
    token = get_token()
    connection_ids = get_connection_ids()
    jobs = start_all_syncs(token, connection_ids)
    wait_for_all(token, jobs)

if __name__ == "__main__":
    main()