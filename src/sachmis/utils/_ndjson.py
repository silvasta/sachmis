import fcntl
import json
import os
import time
import uuid

# NEXT: check for MarkdownRegistry


class ProcessManager:
    def __init__(self, base_dir, log_filename="process_log.jsonl"):
        self.base_dir = base_dir
        self.log_file = os.path.join(base_dir, log_filename)
        self.lock_file = os.path.join(base_dir, ".log_lock")

        # Ensure base directory exists
        os.makedirs(self.base_dir, exist_ok=True)

    def _acquire_fast_lock(self):
        """Creates a very brief lock just for the millisecond of appending."""
        lock_fd = os.open(self.lock_file, os.O_RDWR | os.O_CREAT)
        # fcntl.LOCK_EX = Exclusive lock, fcntl.LOCK_NB = Non-blocking
        while True:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return lock_fd
            except BlockingIOError:
                # Lock is busy, wait a tiny fraction of a second and retry
                time.sleep(0.01)

    def _release_lock(self, lock_fd):
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)

    def get_next_local_id(self, prefix="job_"):
        """
        Finds the next incremental ID locklessly using atomic mkdir.
        """
        current_id = 1
        while True:
            target_dir = os.path.join(
                self.base_dir, f"{prefix}{current_id:04d}"
            )
            try:
                # os.mkdir is ATOMIC. If two processes try this at the exact
                # same time, one will succeed, the other gets FileExistsError.
                os.mkdir(target_dir)
                return current_id, target_dir
            except FileExistsError:
                # Someone else beat us to this ID, try the next one instantly.
                current_id += 1

    def register_task(self, prefix="job_", topic="init"):
        """
        Claims an ID and appends the registration to the JSONL file.
        """
        # 1. Get the ID locklessly (Zero delay)
        local_id, task_dir = self.get_next_local_id(prefix)
        task_uuid = str(uuid.uuid4())

        record = {
            "timestamp": time.time(),
            "local_id": local_id,
            "task_id": task_uuid,
            "path": task_dir,
            "topic": topic,
            "status": "reserved",
        }

        # 2. Append to JSONL with a microsecond-duration lock
        lock_fd = self._acquire_fast_lock()
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(record) + "\n")
        finally:
            self._release_lock(lock_fd)

        return record

    def update_topic(self, task_record, new_topic, status="working"):
        """
        Appends an update for an existing task.
        """
        update_record = {
            "timestamp": time.time(),
            "local_id": task_record["local_id"],
            "task_id": task_record["task_id"],
            "path": task_record["path"],
            "topic": new_topic,
            "status": status,
        }

        lock_fd = self._acquire_fast_lock()
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(update_record) + "\n")
        finally:
            self._release_lock(lock_fd)


# --- Example Usage ---
# manager = ProcessManager("/tmp/shared_project_root")
# my_task = manager.register_task(prefix="level1_")
# print(f"Claimed ID: {my_task['local_id']} at {my_task['path']}")
# manager.update_topic(my_task, new_topic="data_processing")
