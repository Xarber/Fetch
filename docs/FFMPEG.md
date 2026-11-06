# FFmpeg

FFmpeg and FFprobe are external server-side tools, never invoked on iOS. yt-dlp handles merging, audio extraction/conversion, metadata and subtitle postprocessors. Output codec choices are from a closed schema. No shell and no untrusted argument interpolation are used.

After download, FFprobe validates the artifact and its streams. The compatibility preset preserves H.264/AAC MP4 when already suitable. If video/container/audio is incompatible, a fixed FFmpeg command transcodes to H.264/AAC MP4 with two encoder threads, yuv420p and faststart. Audio-only original uses yt-dlp extraction; MP3/M4A/Opus/FLAC/WAV invoke the appropriate installed encoder. Converting lossy material to FLAC/WAV does not improve fidelity.

Postprocessors receive a local protocol allowlist; Fetch does not ask FFmpeg to resolve external manifests or source URLs. Native yt-dlp downloaders and the guarded proxy handle remote inputs. FFmpeg executes in the job process group, so timeout, cancellation and quota enforcement terminate related processes together. The container caps total CPU/memory and process count.

Progress hooks expose real download counters and postprocessor names. Manual compatibility transcoding reports its stage with indeterminate progress; no synthetic percentage is generated. A job is ready only after FFprobe success, size checks, SHA-256 and atomic finalization.

Tests exercise real video inspection and FFmpeg MP3 conversion from a generated fixture. Not every codec, subtitle/source combination or encoder has been tested. Embedding thumbnails and rich metadata editing are not implemented. Build licensing depends on the actual FFmpeg configuration: capture `ffmpeg -version`/`-buildconf` and encoder/license notices before distributing an image. Debian FFmpeg commonly includes GPL components; do not describe every build as LGPL-only.
