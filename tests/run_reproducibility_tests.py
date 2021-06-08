"""
Execute `run_reproducibility_tests.sh` from Python to allow a container built from
Dockerfile_python to execute these tests, and not create an extra Dockerfile
with only this functionality.
"""
import os
import subprocess


if __name__ == "__main__":
    # Execute shell file in same directory
    file_path = os.path.join("tests", "run_reproducibility_tests.sh")
    subprocess.run(["sh", file_path])
