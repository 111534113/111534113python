#環境檢查員
import sys
import os
print("--- Python Executable ---")
print(sys.executable)
print("\n--- sys.path ---")
for p in sys.path:
    print(p)

try:
    import ttkthemes
    print("\n--- ttkthemes location ---")
    print(ttkthemes.__file__)
except ImportError:
    print("\n--- ttkthemes not found ---")
