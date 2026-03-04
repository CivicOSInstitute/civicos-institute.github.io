# Fundraising Document Producer

Governance-style fundraising document generator.

## Modes
- `grant`
- `donor-ask`
- `corporate-sponsorship`

## Usage
```bash
node scripts/fundraising/create_fundraising_doc.js scripts/fundraising/sample_input.json grant
node scripts/fundraising/create_fundraising_doc.js scripts/fundraising/sample_input.json donor-ask
node scripts/fundraising/create_fundraising_doc.js scripts/fundraising/sample_input.json corporate-sponsorship
```

## DOCX export
```bash
node scripts/fundraising/create_fundraising_doc.js scripts/fundraising/sample_input.json grant --docx
```

Outputs are written to:
- `generated/fundraising/*.md`
- `generated/fundraising/*.docx` (when pandoc is installed)
