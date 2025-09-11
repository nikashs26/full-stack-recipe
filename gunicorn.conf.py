# Gunicorn configuration for Render deployment
# Optimized for free tier memory constraints

import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 10000)}"
backlog = 2048

# Worker processes
workers = 1  # Single worker for free tier
worker_class = "sync"
worker_connections = 100
timeout = 600  # Increased timeout for heavy operations
keepalive = 2
max_requests = 100  # Restart workers after 100 requests to prevent memory leaks
max_requests_jitter = 10

# Memory management
worker_tmp_dir = "/dev/shm"  # Use shared memory for temp files
preload_app = False  # Disable preload to save memory

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "dietary-delight-backend"

# Resource limits
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Graceful handling
graceful_timeout = 30
