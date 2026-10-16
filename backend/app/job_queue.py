"""Redis-backed job queue (RQ) for slow OCR/parse work."""

from __future__ import annotations

import os

from redis import Redis
from rq import Queue
from rq.job import Job

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
QUEUE_NAME = "parse"
JOB_TIMEOUT_S = 300
RESULT_TTL_S = 3600  # results are kept for 1 hour

redis_conn = Redis.from_url(REDIS_URL)
parse_queue = Queue(QUEUE_NAME, connection=redis_conn, default_timeout=JOB_TIMEOUT_S)


def enqueue_parse(file_bytes: bytes, file_name: str) -> str:
	job = parse_queue.enqueue(
		"app.tasks.parse_job",
		file_bytes,
		file_name,
		result_ttl=RESULT_TTL_S,
		failure_ttl=RESULT_TTL_S,
	)
	return job.id


def fetch_job(job_id: str) -> Job | None:
	try:
		return Job.fetch(job_id, connection=redis_conn)
	except Exception:
		return None
