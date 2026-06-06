# T-015 DESIGN - hands-free multi-take vocal recorder

**Author:** Mini - 2026-06-06  
**Scope:** interaction + architecture for standalone voice/foot-pedal control, multi-take recording, and lyric-line punch-in. No hardware dependency required for this design.

---

## 0. Product shape

This app is not a DAW. It is a focused vocal capture machine:

1. Load a song package: backing WAV/AIFF/MP3 + lyrics text.
2. Align lyric lines to timecode once.
3. Record full takes while the backing plays.
4. Re-record specific lyric lines hands-free.
5. Keep every take/segment non-destructively.
6. Export raw WAVs + a simple comp manifest for Logic / AI post-production.

Core principle: **the foot pedal gates intent; voice supplies detail only when safe.** Singing and voice commands share the same microphone, so the app must not listen for arbitrary commands during active singing.

---

## 1. Interaction Model

### Main states

| State | Meaning | Allowed inputs |
|---|---|---|
| `IDLE` | Song loaded, transport stopped | pedal, voice |
| `READY` | Backing positioned, waiting to record/play | pedal, voice |
| `PLAYING` | Backing plays, not recording | pedal, voice in gaps |
| `RECORDING_FULL_TAKE` | Backing plays and mic records a complete take | pedal only, emergency voice only after pedal hold |
| `PUNCH_ARMED` | Target lyric line selected, preroll pending | pedal, voice |
| `RECORDING_PUNCH` | Recording a replacement segment for one line/range | pedal only |
| `REVIEW` | Last take/segment can be replayed, accepted, redone, labeled | pedal, voice |
| `EXPORTING` | Rendering/copying WAVs and manifests | none except cancel |

### Default session loop

1. Singer loads `Song`.
2. App shows current lyric line, next line, transport time, selected take, and input level.
3. Singer says or pedals: `start`.
4. Backing starts with count-in; full take records.
5. Singer taps pedal to stop.
6. App saves `Take 001` immediately.
7. Singer can say: `again`, `new take`, `play last`, `re-sing that line`, `re-sing line 12`, `export`.

### UI assumptions

The first version can be a desktop app or terminal prototype, but the interaction should be stable:

- Big status: `IDLE`, `RECORDING`, `PUNCH: line 18`.
- Lyrics panel: previous/current/next line with line numbers.
- Take list: take number, timestamp, type, duration, notes.
- Level meters: input peak, output transport position.
- Transport timeline: backing time + lyric line boundaries.
- No mixing UI, plugins, pitch tools, or DAW-style editing.

---

## 2. Command Grammar

### Design rules

- Commands are short, explicit, and enumerable.
- Commands are accepted only in states where they make sense.
- During recording, voice recognition is normally muted.
- A pedal hold opens a temporary push-to-talk command window.
- Every command resolves to a typed intent, not free-form text.

### Canonical command intents

```text
Transport:
  start
  play
  stop
  pause
  resume
  go back
  go to beginning

Recording:
  record
  new take
  again
  keep it
  discard last
  play last

Punch-in:
  re-sing that line
  re-sing this line
  re-sing previous line
  re-sing next line
  re-sing line <number>
  re-sing from <line number> to <line number>
  punch chorus
  punch verse <number>

Navigation:
  next line
  previous line
  go to line <number>
  go to chorus
  go to verse <number>

Export:
  export all takes
  export selected comp
  export session

Utility:
  mark good
  mark bad
  note <short phrase>
  undo
  cancel
```

### Spoken grammar examples

The parser should normalize synonyms into one intent:

| Spoken phrase | Intent |
|---|---|
| "start backing" | `START_PLAYBACK` |
| "record take" | `START_FULL_TAKE` |
| "one more" | `NEW_TAKE` |
| "re-sing that line" | `PUNCH_CURRENT_LINE` |
| "do line twelve again" | `PUNCH_LINE(line_id=12)` |
| "from line twelve to fourteen" | `PUNCH_RANGE(start=12,end=14)` |
| "keep that" | `ACCEPT_LAST` |
| "throw that away" | `REJECT_LAST` |

### Parser architecture

```text
audio/PTT window
  -> STT engine or typed command in prototype
  -> phrase normalizer
  -> constrained grammar parser
  -> intent validator for current state
  -> command bus
  -> transport/take/alignment services
```

For the prototype, the STT layer can be replaced by keyboard text commands. The rest of the system should still consume the same typed intents.

---

## 3. Foot-Pedal Push-To-Talk Flow

### Pedal roles

Assume a three-switch pedal when available, but support one-switch fallback.

| Control | Tap | Hold | Double tap |
|---|---|---|---|
| Left | go back / previous line | rewind while held | go to previous section |
| Center | start/stop record or play | push-to-talk command window | redo last line |
| Right | next line / accept | fast-forward while held | mark good |

One-switch fallback:

| Gesture | Meaning |
|---|---|
| Tap | start/stop current action |
| Hold | push-to-talk |
| Double tap | redo current/last lyric line |
| Triple tap | cancel / stop all |

### Push-to-talk sequence

1. Singer holds center pedal.
2. App ducks backing playback by configurable amount, for example `-12 dB`, or pauses if stopped.
3. App opens command listening window after a short debounce, for example `120 ms`.
4. Singer speaks command: "re-sing line 12".
5. Singer releases pedal.
6. App stops listening immediately.
7. Command is parsed and confirmed with a short visual/audio cue.
8. App executes state transition.

### Why this avoids false triggers

- While recording vocals, STT is disabled unless the pedal is held.
- The app records the vocal take continuously, but command audio captured during PTT is tagged as `control_audio` and excluded from take export.
- If PTT is held during an active take, the app creates an automatic split boundary before and after the command window so the musical audio remains cleanly segmentable.

### Critical safeguards

- `STOP_ALL` must work from any state via long hold plus tap, or triple tap in one-switch mode.
- Commands that delete or discard only mark data inactive; they never remove WAV files during the session.
- Ambiguous commands require confirmation: "line 12 or current line?".
- If confidence is low, app shows/hears: "command not understood" and returns to the prior state.

---

## 4. Punch-In Interaction

### "Re-sing that line"

`that line` resolves in this priority order:

1. Current lyric line at transport playhead.
2. Last line recorded in the latest take.
3. Line selected in UI.
4. If none, ask for a line number.

### Punch flow

1. Resolve target line or range to `line_id` values.
2. Look up cached timecode: `start_sec`, `end_sec`.
3. Apply musical safety margins:
   - `preroll_sec`: default `2.0` or one bar if tempo known.
   - `postroll_sec`: default `0.5`.
   - `record_start_sec`: `line.start_sec - lead_in_sec`, default `0.2`.
   - `record_end_sec`: `line.end_sec + tail_sec`, default `0.5`.
4. Seek backing to `line.start_sec - preroll_sec`.
5. Play preroll without recording, optionally with count cue.
6. Auto-drop into recording at `record_start_sec`.
7. Auto-drop out at `record_end_sec`, or allow pedal tap to stop early.
8. Save new `PunchSegment` as its own WAV.
9. Set it as the active comp choice for that lyric line unless user rejects it.

### Repeat loop

After a punch segment:

- Tap center: replay punch region.
- Double tap center: record same line again.
- Tap right: accept and advance to next line.
- Tap left: go to previous line.
- Hold center and say "line 14": jump to another line.

---

## 5. Take Data Model

Use plain JSON for MVP; SQLite can replace it later without changing concepts.

### Entities

```text
Project
  id
  title
  artist
  sample_rate
  bit_depth
  created_at
  backing_asset_id
  lyric_document_id
  active_comp_id

BackingAsset
  id
  path
  duration_sec
  sample_rate
  channels
  hash

LyricDocument
  id
  language
  sections[]
  lines[]

LyricLine
  id
  section_id
  line_number
  text
  normalized_text
  start_sec
  end_sec
  confidence
  source

Take
  id
  take_number
  type: full | punch | scratch | guide
  wav_path
  started_at
  backing_start_sec
  backing_end_sec
  record_start_sec
  record_end_sec
  sample_rate
  bit_depth
  channels
  status: active | rejected | archived
  markers[]
  notes[]

TakeSegment
  id
  take_id
  line_ids[]
  wav_path
  backing_start_sec
  backing_end_sec
  wav_start_sec
  wav_end_sec
  kind: full_take_region | punch_region
  status: active | rejected

Comp
  id
  name
  created_at
  choices[]

CompChoice
  line_id
  take_id
  segment_id
  crossfade_in_ms
  crossfade_out_ms
  gain_db
```

### Non-destructive rule

No punch overwrites an old take. A punch creates a new `Take` or `TakeSegment`, then updates `CompChoice`. Raw audio files remain immutable after write.

### Minimal JSON shape

```json
{
  "project": {
    "id": "song_20260606_001",
    "title": "Demo Song",
    "sample_rate": 48000,
    "bit_depth": 24,
    "active_comp_id": "comp_main"
  },
  "lyrics": {
    "lines": [
      {
        "id": "L0012",
        "line_number": 12,
        "section": "chorus",
        "text": "I keep running toward the light",
        "start_sec": 48.230,
        "end_sec": 51.900,
        "confidence": 0.91,
        "source": "alignment"
      }
    ]
  },
  "takes": [
    {
      "id": "take_001",
      "take_number": 1,
      "type": "full",
      "wav_path": "audio/takes/take_001_full.wav",
      "backing_start_sec": 0.0,
      "backing_end_sec": 183.2,
      "status": "active"
    }
  ],
  "segments": [
    {
      "id": "seg_017",
      "take_id": "take_006",
      "line_ids": ["L0012"],
      "wav_path": "audio/punches/take_006_L0012.wav",
      "backing_start_sec": 48.030,
      "backing_end_sec": 52.400,
      "kind": "punch_region",
      "status": "active"
    }
  ],
  "comps": [
    {
      "id": "comp_main",
      "name": "Main",
      "choices": [
        {
          "line_id": "L0012",
          "take_id": "take_006",
          "segment_id": "seg_017",
          "crossfade_in_ms": 25,
          "crossfade_out_ms": 50,
          "gain_db": 0.0
        }
      ]
    }
  ]
}
```

---

## 6. Lyric to Timecode Mapping

### Inputs

- Required: plain lyric text with line breaks.
- Required: backing track.
- Optional but recommended: first full vocal take or guide vocal.
- Optional: song tempo map / section labels.

### Alignment sources

| Source | When used | Confidence |
|---|---|---|
| manual tap/marker | prototype or correction | high if reviewed |
| WhisperX on guide/full take | normal workflow | medium-high |
| MFA | precision fallback | high but heavier |
| estimated tempo grid | before audio alignment | low |

### Alignment workflow

1. Parse lyrics into sections and lines.
2. Normalize each line:
   - lowercase
   - remove punctuation
   - expand common contractions only if STT output needs it
   - preserve original display text
3. Create provisional line ids: `L0001`, `L0002`, etc.
4. Run forced alignment against guide/full vocal.
5. Convert word-level timestamps into line spans:
   - line start = first word start
   - line end = last word end
   - add optional tail padding for sustained singing
6. Store confidence per line.
7. Flag low-confidence lines for manual review.
8. Cache mapping in `alignment/lines.v1.json`.

### Timecode semantics

- Timecodes are always in backing-track seconds.
- A take records local WAV time and backing time separately.
- `backing_start_sec` lets any take segment map back onto the song timeline.
- Do not rely on wall-clock time for musical alignment.

### Line boundary correction

The app needs two simple correction commands:

```text
set line start
set line end
```

Correction flow:

1. Play around selected line.
2. User taps pedal at the desired boundary.
3. App writes a manual override to the line timecode.
4. Alignment source becomes `manual`.

---

## 7. Architecture

### Service layout

```text
App Shell
  UI / terminal view
  command feedback
  session lifecycle

Command Layer
  pedal adapter
  push-to-talk controller
  STT adapter or typed command adapter
  grammar parser
  intent validator

Transport Engine
  backing playback
  seek/preroll/drop-in/drop-out
  clock source
  state machine

Recording Engine
  mic capture
  WAV writer
  take finalizer
  punch segment writer

Lyric Engine
  lyric parser
  alignment importer/runner
  line lookup
  boundary corrections

Take Store
  project manifest
  immutable audio paths
  take/segment/comp metadata
  autosave

Export Engine
  raw take copier
  selected comp renderer or manifest export
  Logic-friendly folder layout
```

### Event flow

```text
Pedal/STT/Keyboard
  -> CommandIntent
  -> StateMachine.apply(intent)
  -> TransportCommand / RecordCommand / StoreCommand
  -> domain event
  -> autosave project.json
  -> UI update
```

Example:

```text
PTT "re-sing line 12"
  -> PUNCH_LINE(L0012)
  -> resolve line timecode
  -> set state PUNCH_ARMED
  -> seek to preroll
  -> play backing
  -> record punch WAV
  -> create Take + TakeSegment
  -> update active CompChoice
  -> set state REVIEW
```

### Clocks and sync

The transport engine owns the timeline. All services ask it for current backing time. The recording engine writes actual WAV samples, then records metadata that maps WAV sample offsets to backing-track time.

For Swift later, use the audio engine render time / sample time as the authoritative clock. For Python MVP, use PortAudio stream callback frame counts rather than UI timers.

---

## 8. File and Export Layout

### Working project folder

```text
Song_Title.session/
  project.json
  README.txt
  backing/
    backing_original.wav
    backing_render_48k.wav
  lyrics/
    lyrics.txt
    lyrics.normalized.json
  alignment/
    lines.v1.json
    corrections.json
  audio/
    takes/
      take_001_full.wav
      take_002_full.wav
    punches/
      take_003_L0012.wav
      take_004_L0012-L0014.wav
    control/
      20260606_031455_ptt_command.wav
  comps/
    comp_main.json
  exports/
    raw/
    comp/
```

### Export: raw takes

```text
exports/raw/
  Song_Title_backing.wav
  Song_Title_take_001_full.wav
  Song_Title_take_002_full.wav
  Song_Title_take_003_L0012_punch.wav
  Song_Title_take_004_L0012-L0014_punch.wav
  Song_Title_session_manifest.json
  Song_Title_lyrics_timecoded.csv
```

### Export: selected comp

Two MVP options:

1. **Manifest-only comp**: export all referenced WAVs plus `comp_main.json` so Logic/AI can rebuild the comp.
2. **Rendered comp WAV**: render one mono/stereo vocal WAV by placing chosen segments on the backing timeline with short crossfades.

For MVP, prefer both:

```text
exports/comp/
  Song_Title_vocal_comp_main.wav
  Song_Title_comp_main.json
  Song_Title_comp_sources/
    take_001_full.wav
    take_003_L0012_punch.wav
  Song_Title_lyrics_timecoded.csv
```

### CSV for human/debug use

```csv
line_id,line_number,section,start_sec,end_sec,text,active_take,active_segment
L0012,12,chorus,48.230,51.900,I keep running toward the light,take_006,seg_017
```

---

## 9. MVP Build Order

1. **Typed-command prototype:** load backing + lyrics, accept typed commands, write fake take metadata.
2. **Audio loop:** play backing while recording full WAV takes.
3. **Pedal adapter:** map tap/hold/double tap to typed intents.
4. **Line timecodes:** import manual `lyrics_timecoded.csv` before forced alignment exists.
5. **Punch-in:** seek, preroll, record line segment, update comp choice.
6. **PTT voice:** pedal hold opens command capture; parse constrained command grammar.
7. **Alignment:** generate `lines.v1.json` from first full take or guide vocal.
8. **Export:** raw WAVs + comp manifest, then rendered comp WAV.

This order keeps the core product testable without the real studio rig: keyboard commands can stand in for pedal, generated/silent audio can stand in for mic input, and manual timecodes can stand in for forced alignment.

---

## 10. Open Decisions for IA10 Synthesis

- One-switch pedal first or three-switch pedal first. Design supports both; three-switch is faster for real sessions.
- Whether `PTT during active full-take` should pause recording, split the take, or keep recording with a control-audio mask. My recommendation: split/mark, never silently include command audio in export.
- Whether MVP exports rendered comp WAV immediately. My recommendation: yes, but keep manifest export as the authoritative handoff because Logic/AI tools may prefer raw sources.
- Whether alignment is run before any recording. My recommendation: allow manual CSV first, then align from first full take after the audio loop works.
