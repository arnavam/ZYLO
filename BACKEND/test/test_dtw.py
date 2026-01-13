import numpy as np
from dtw import dtw

x = np.array(["a", "b", "c"]).reshape(-1, 1)
y = np.array(["a", "b", "d"]).reshape(-1, 1)
dist_func = lambda x, y: 0 if x == y else 1

try:
    result = dtw(x, y, dist_func)
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    
    # Try unpacking
    try:
        d, _, _, _ = result
        print(f"Unpacked distance: {d}")
    except Exception as e:
        print(f"Unpack failed: {e}")
        
    # Try accessing distance attribute
    if hasattr(result, 'distance'):
        print(f"Distance attribute: {result.distance}")
    elif hasattr(result, 'normalizedDistance'):
        print(f"Normalized distance attribute: {result.normalizedDistance}")
        
except Exception as e:
    print(f"DTW call failed: {e}")
