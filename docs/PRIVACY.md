# Privacy & Data Handling (pediatric medical data)

This tool processes video of **children**, in a **clinical** context. Treat all
data as sensitive medical data.

## Built-in protections
- **Local-only.** No network calls anywhere in the pipeline. Models are local
  files; storage is a local SQLite database. Nothing is uploaded.
- **Face blur.** `equipose.privacy.blur_faces` Gaussian-blurs a region around
  the face. Apply it to **any** frame/thumbnail written to disk or shown in an
  export before it leaves the workstation.
- **No names in the database.** Patients are keyed by an arbitrary code
  (`patient_id`). Do not put real names in `patient_id` or `notes`.
- **Raw video is gitignored** (`*.mp4`, `*.mov`, `data/`, `*.sqlite`). Never
  commit recordings, the database, or exports.

## Operator responsibilities
- Obtain informed consent from guardians before recording, covering storage and
  research use.
- Keep recordings and the SQLite database on an encrypted, access-controlled
  disk. Delete raw video per your retention agreement.
- Share only de-identified, face-blurred exports.
- This is a **research/screening** aid, not a diagnostic device. Clinical
  decisions remain with the therapist/physician.

## Therapist labels
Labels collected via the labeling sink are stored locally for **future** model
training. They contain no media — only `(session_id, frame_idx, label,
therapist_id, timestamp)`.
