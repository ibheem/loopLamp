#!/usr/bin/env bash
set -e

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.11 is required, but 'python3' was not found."
  echo "Install Python 3.11.9 and rerun bootstrap.sh."
  exit 1
fi

python_version="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
python_major_minor="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

if [ "$python_major_minor" != "3.11" ]; then
  echo "Python 3.11 is required, but found Python ${python_version}."
  echo "Please switch to Python 3.11.9 and rerun bootstrap.sh."
  exit 1
fi

echo "Using Python ${python_version}"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "Environment ready!"
