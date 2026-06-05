# SoundFont

Put a General MIDI `.sf2` file in this directory before rendering WAV audio.

Recommended source for M0:

- **GeneralUser GS** by S. Christian Collins: https://schristiancollins.com/generaluser.php

Large binary `.sf2` files are intentionally ignored by git. The CLI will still export
`out/demo.mid` without a soundfont, and will render `out/demo.wav` automatically when
both a `.sf2` file here and a `fluidsynth` binary are available.

Example:

```sh
mkdir -p soundfonts
curl -L -o /tmp/generaluser.zip \
  'https://www.dropbox.com/scl/fi/db4y0l478l4v4b5i7vddf/GeneralUser_GS_1.472.zip?rlkey=8qayemzudropfey357hccn3ce&st=7lbhve6a&dl=1'
unzip /tmp/generaluser.zip -d soundfonts
```
