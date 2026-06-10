import urllib.request
import json

data = json.loads(urllib.request.urlopen('https://tankermap.com/api/vessels/live?fields=map').read())

def in_box(v, box):
    lat = v.get('latitude', 0)
    lon = v.get('longitude', 0)
    return box[0] <= lat <= box[1] and box[2] <= lon <= box[3]

def calc(box):
    return sum(v.get('deadweight',0)*0.85*7.33 for v in data if in_box(v, box) and 'oil' in v.get('vessel_type','').lower() and v.get('speed_knots',0)>3)/1e6

boxes = [
    [0.5, 6.5, 98.5, 104.5],  # Original
    [-1.0, 8.0, 95.0, 106.0], # Wide
    [1.0, 5.0, 98.0, 102.0],  # Medium
    [1.5, 4.0, 100.0, 102.0], # Small
    [2.0, 4.0, 100.5, 101.5], # Smaller
]

for b in boxes:
    print(f"Box {b}: {calc(b):.1f} mb")

