from pymongo import MongoClient, monitoring


class BenchListener(monitoring.CommandListener):
    def __init__(self, watched_commands=None):
        self.watched = set(watched_commands or [])
        self.latencies = []

    def started(self, event):
        pass

    def succeeded(self, event):
        if not self.watched or event.command_name in self.watched:
            self.latencies.append(event.duration_micros)

    def failed(self, event):
        pass
