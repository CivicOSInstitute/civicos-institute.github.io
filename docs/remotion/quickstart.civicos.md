# Remotion Quick Start (CivicOS Institute)

## 1) Create project
```bash
npx create-video@latest
```

## 2) Enter project
```bash
cd <your-project-name>
```

## 3) Start dev
```bash
npm run dev
```

## 4) If template uses separate studio command
```bash
npm run remotion
```

## 5) CivicOS baseline structure

```text
assets/
  2026-03-campaign-name/
src/
  compositions/
  scenes/
```

## 6) Add one standardized render command

Example:
```bash
npx remotion render src/index.ts CivicOSDonorUpdate30s out/donor-update-30s.mp4
```

## 7) Team rule

- Keep scripts reproducible.
- Keep naming consistent.
- Keep outputs in `out/` with date or campaign tags.
