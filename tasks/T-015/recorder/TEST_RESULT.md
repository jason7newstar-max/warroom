# T-015 M1 Built-In Device Proof

Run on 2026-06-06 from:

```bash
cd /Users/pinnyc/codex-work/warroom/tasks/T-015/recorder
.venv/bin/python recorder.py --self-test --seconds 4 --input-device 2 --output-device 3
```

Detected devices:

```text
2: iMac Microphone (1 in, 0 out, default_sr=44100)
3: iMac Speakers (0 in, 2 out, default_sr=44100)
```

Result:

```text
SELF-TEST PASS
WAV=/Users/pinnyc/codex-work/warroom/tasks/T-015/recorder/sessions/m1_self_test/take_002_20260606_035930.wav
JSON=/Users/pinnyc/codex-work/warroom/tasks/T-015/recorder/sessions/m1_self_test/take_002_20260606_035930.json
duration=4.000s samplerate=44100
```

Sidecar summary:

```json
{
  "take": 2,
  "device": {
    "input": "iMac Microphone",
    "output": "iMac Speakers",
    "input_device_index": 2,
    "output_device_index": 3
  },
  "samplerate": 44100,
  "duration": 4.0,
  "software_monitoring": false
}
```
