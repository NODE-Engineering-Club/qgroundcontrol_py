import time

class MissionLogger:
    def __init__(self):
        self.logs = []

    def log(self, message):
        timestamp = time.strftime("[%H:%M:%S]")
        log_entry = f"{timestamp} {message}"
        print(log_entry)
        self.logs.append(log_entry)

    def get_logs(self):
        return self.logs

    def save_to_file(self, path="mission_log.txt"):
        with open(path, "w") as f:
            for entry in self.logs:
                f.write(entry + "\n")
