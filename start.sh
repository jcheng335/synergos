#!/bin/bash
cd synergos && gunicorn --bind 0.0.0.0:${PORT:-8080} wsgi:application