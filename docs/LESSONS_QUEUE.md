# Lessons queue

Lessons from sessions that would still be true in a different app, waiting to be written to the Knowledge Base. Not ledger items.

- [ ] (2026-11-17) Pre-writing an emulator's config to skip the first-run wizard can leave it silent: Cemu's `<Audio><api>` defaulted to 0 (DirectSound, absent on Linux) and `<TVDevice>` was empty, so it opened no audio stream and logged no error. PipeWire showing no stream from the app, with all sinks suspended, was the tell; fix was api=3 (Cubeb) + device `default`, edited while the app was closed because it rewrites the file on exit.
