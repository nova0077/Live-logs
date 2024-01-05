from flask import Flask, Response, render_template, request
from flask_sse import sse
import os
import time

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost:6379/0"

app.register_blueprint(sse, url_prefix="/stream")

LOG_FILE_DIRECTORY = os.path.join(".")  # TODO: Use env variable for loading
LOG_FILE_NAME = "debug.log"

last_n_lines = []
clients = set()


def read_last_lines(file_path, n=10):
    with open(file_path, "r") as f:
        lines = "".join(f.readlines()[-n:])
        return lines


class LogFileHandler(PatternMatchingEventHandler):
    def __init__(self, *args, **kwargs):
        self.file_size = os.path.getsize(LOG_FILE_NAME)
        super().__init__(*args, **kwargs)

    def on_modified(self, event):
        # Check for file modification
        global last_n_lines
        current_size = os.path.getsize(LOG_FILE_NAME)

        if current_size > self.file_size:
            with open(LOG_FILE_NAME, "r") as f:
                f.seek(self.file_size)
                new_content = f.read(current_size - self.file_size)
                print("new content::", new_content)
                self.file_size = current_size
                for client in clients:
                    with app.app_context():
                        sse.publish(new_content, type="log_update")


observer = Observer()
observer.schedule(LogFileHandler(patterns=[LOG_FILE_NAME]), path=LOG_FILE_DIRECTORY)


@app.route("/")
def index():
    data = read_last_lines(LOG_FILE_NAME) or "log is empty"
    return render_template("index.html", data=data)
    # return render_template("index.html", data=temp_data)

@app.route("/init-logs")
def init_logs():
    data = read_last_lines((LOG_FILE_NAME)) or ""
    return data

@app.after_request
def init_stream(res):
    if "/stream" in request.path:
        client_id = (
            request.args.get("client_id") or "root123"
        )  # Generate string client id
        last_10_lines = read_last_lines(LOG_FILE_NAME) or ""
        sse.publish(last_10_lines, type="log_update")
        clients.add(client_id)
        return res
    return res


if __name__ == "__main__":
    observer.start()

    app.run(debug=True)
