import time

def current_timestamp():
    return time.time()

def print_banner(msg: str):
    line = "=" * 60
    print(f"\n{line}\n{msg}\n{line}\n")
