import os
import multiprocessing

# Number of workers: (2 x $NUM_CORES) + 1 is a common rule of thumb
# For Koyeb, you can set this via an environment variable or keep it fixed
workers = int(os.environ.get('GUNICORN_WORKERS', 4))
bind = "0.0.0.0:8000"
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"