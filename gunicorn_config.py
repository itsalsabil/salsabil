import multiprocessing
import os

# Gunicorn configuration file

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '5001')}"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'salsabil-rh'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (si nécessaire)
# keyfile = None
# certfile = None
