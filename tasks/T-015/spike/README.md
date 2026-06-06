# T-015 Spike · Apogee Duet 2 Full-Duplex I/O

This spike lists CoreAudio devices through PortAudio, finds the Apogee Duet 2, then plays a low backing test tone while recording input for about 3 seconds.

```bash
cd /Users/pinnyc/codex-work/warroom/tasks/T-015/spike
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python duet_full_duplex_spike.py
```

Useful reruns:

```bash
.venv/bin/python duet_full_duplex_spike.py --list-only
.venv/bin/python duet_full_duplex_spike.py --device-regex 'Duet|Apogee'
.venv/bin/python duet_full_duplex_spike.py --input-regex 'iMac Microphone' --output-regex 'iMac Speakers'
```

Generated WAV files are ignored by git.
