import torch
import sys

# Usage: python extract_speakers.py path/to/speakers.pth
if len(sys.argv) != 2:
    print('Usage: python extract_speakers.py path/to/speakers.pth')
    sys.exit(1)

speakers_path = sys.argv[1]

try:
    data = torch.load(speakers_path, map_location='cpu')
    if isinstance(data, dict):
        if 'speakers' in data:
            speakers = data['speakers']
        else:
            speakers = data
        print('Speakers:')
        if isinstance(speakers, dict):
            for idx, name in enumerate(speakers):
                print(f'{idx}: {name}')
        elif isinstance(speakers, list):
            for idx, name in enumerate(speakers):
                print(f'{idx}: {name}')
        else:
            print(speakers)
    else:
        print('Unknown format:', type(data))
except Exception as e:
    print('Failed to load speakers.pth:', e) 