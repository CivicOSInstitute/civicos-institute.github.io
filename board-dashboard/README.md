# CivicOS Board Dashboard

## Governance Hub Content Locations

Place governance and meeting assets here:

- Governance index data (drives Governance + Meetings tabs):
  - `board-dashboard/data/governance_index.json`
- Agenda queue (Agenda Builder persistence):
  - `board-dashboard/data/next_agenda.json`
- Governance documents linked in the Governance tab:
  - `board-dashboard/documents/`
  - Example files: `bylaws.pdf`, `charter.pdf`, `board-roster.pdf`, `committee-structure.pdf`, `conflict-of-interest-policy.pdf`
- Meeting recordings and artifacts linked in the Meetings tab:
  - `board-dashboard/recordings/<YYYY-MM-DD>/`
  - Example files per meeting: `minutes.pdf`, `transcript.txt`, `audio.mp3`, `video.mp4`

## Notes

- Role-based behavior is preserved:
  - `provisional`: read-only (no submit/edit/delete)
  - `advisory` and `board`: can submit, edit, and delete agenda items
- Governance and meeting links are rendered as clean cards/lists (no raw JSON visible to users).
