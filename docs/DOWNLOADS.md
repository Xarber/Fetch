# Downloads

A URL inspection is separate from job creation. An authorized selection is validated against inspection formats; custom IDs cannot contain operators or arbitrary flags. Presets are compiled by the server. A client idempotency key deduplicates job creation across uncertain responses.

Server pipeline:

1. Durable queued job, ordered by descending priority and creation time.
2. Singleton worker transaction claims the job; child process starts a guarded proxy.
3. yt-dlp retrieves source data and emits actual byte/speed/ETA fields.
4. FFmpeg postprocessing, optional compatibility conversion, FFprobe validation.
5. Streaming SHA-256 and atomic final artifact path; state becomes ready.
6. Client separately requests a transfer capability and saves a verified local copy.

Pausing a queued job stops scheduling it. Pausing a running download terminates its process group; resuming restarts yt-dlp and may reuse its `.part` files if the source supports it. Postprocessing cannot pause; use cancel and retry. Cancellation preserves the historical job but cleans worker intermediates after process termination. Failed media can be retried; original intermediate data may remain until explicit deletion. Server restart requeues interrupted active work, without creating a second logical job.

Queue concurrency applies to downloads and conversions together. Browser/native URL batch import is sequential inspection followed by individual creation; an error leaves already-created jobs visible and reports the successful count. The backend also supports atomic batch creation for pre-inspected entries.

Limitations: no playlist item selection, drag reordering, scheduled charging policy, precise iOS background schedule, or automatic playlist expansion. Priority updates and Wi-Fi-only native transfers are implemented. REST snapshots reconcile disconnected clients; progress revisions distinguish newer authoritative state from duplicates.
