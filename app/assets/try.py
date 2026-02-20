import sys
import os

def main():
    print(f"DEBUG: argv={sys.argv!r}")  # show how you called the script
    # ... your existing argument checks ...
    if len(sys.argv) != 2:
        print("ERROR: Expected exactly 1 input argument (input_path).")
        sys.exit(2)

    input_path = sys.argv[1]
    print(f"DEBUG: input_path={input_path!r}, exists={os.path.exists(input_path)}")

    if not os.path.exists(input_path):
        print(f"ERROR: Input path not found: {input_path}")
        sys.exit(2)

    # rest of your logic...