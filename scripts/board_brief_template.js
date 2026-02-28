const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, ExternalHyperlink, HeadingLevel,
  BorderStyle, WidthType, ShadingType, PageNumber, LevelFormat,
  TabStopType, TabStopPosition
} = require('docx');
const fs = require('fs');

const DATE = "February 27, 2026";
const BRAND_BLUE = "1B3A6B";
const BRAND_LIGHT = "E8EEF7";
const ACCENT = "C8392B";
const GRAY = "666666";

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

// ── Helpers ───────────────────────────────────────────────────────────────────

const spacer = (before = 120, after = 120) =>
  new Paragraph({ children: [new TextRun("")], spacing: { before, after } });

const rule = () => new Paragraph({
  children: [new TextRun("")],
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND_BLUE, space: 1 } },
  spacing: { before: 0, after: 160 }
});

const sectionHeader = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text: text.toUpperCase(), color: BRAND_BLUE, bold: true, size: 22, font: "Arial" })],
  spacing: { before: 320, after: 120 }
});

const bullet = (text, hyperlink = null) => {
  const run = hyperlink
    ? new ExternalHyperlink({ children: [new TextRun({ text, style: "Hyperlink", size: 20, font: "Arial" })], link: hyperlink })
    : new TextRun({ text, size: 20, font: "Arial" });
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: [run],
    spacing: { before: 60, after: 60 }
  });
};

const label = (text) => new TextRun({ text, bold: true, size: 19, font: "Arial", color: BRAND_BLUE });
const body  = (text) => new TextRun({ text, size: 19, font: "Arial" });
const muted = (text) => new TextRun({ text, size: 18, font: "Arial", color: GRAY, italics: true });

// ── Signal Card ───────────────────────────────────────────────────────────────

const signalCard = (num, headline, source, sourceUrl, relatedVideo, videoUrl,
                    why, riskOpportunity, nextStep) => [
  new Paragraph({
    children: [new TextRun({ text: `${num}.  ${headline}`, bold: true, size: 22, font: "Arial", color: BRAND_BLUE })],
    spacing: { before: 240, after: 80 }
  }),
  new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [1600, 7760],
    rows: [
      new TableRow({ children: [
        new TableCell({ borders, width: { size: 1600, type: WidthType.DXA },
          shading: { fill: BRAND_LIGHT, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [label("Source")] })] }),
        new TableCell({ borders, width: { size: 7760, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [
            body(`${source}  `),
            new ExternalHyperlink({ children: [new TextRun({ text: "→ Read article", style: "Hyperlink", size: 19, font: "Arial" })], link: sourceUrl })
          ]})] })
      ]}),
      new TableRow({ children: [
        new TableCell({ borders, width: { size: 1600, type: WidthType.DXA },
          shading: { fill: BRAND_LIGHT, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [label("Related")] })] }),
        new TableCell({ borders, width: { size: 7760, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: videoUrl
            ? [body(`${relatedVideo}  `), new ExternalHyperlink({ children: [new TextRun({ text: "→ Watch", style: "Hyperlink", size: 19, font: "Arial" })], link: videoUrl })]
            : [muted("No related video this cycle")]
          })] })
      ]}),
      new TableRow({ children: [
        new TableCell({ borders, width: { size: 1600, type: WidthType.DXA },
          shading: { fill: BRAND_LIGHT, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [label("Why it matters")] })] }),
        new TableCell({ borders, width: { size: 7760, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [body(why)] })] })
      ]}),
      new TableRow({ children: [
        new TableCell({ borders, width: { size: 1600, type: WidthType.DXA },
          shading: { fill: BRAND_LIGHT, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [label("Risk / Opportunity")] })] }),
        new TableCell({ borders, width: { size: 7760, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [body(riskOpportunity)] })] })
      ]}),
      new TableRow({ children: [
        new TableCell({ borders, width: { size: 1600, type: WidthType.DXA },
          shading: { fill: "FFF3CD", type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: "Next Step", bold: true, size: 19, font: "Arial", color: ACCENT })] })] }),
        new TableCell({ borders, width: { size: 7760, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: nextStep, bold: true, size: 19, font: "Arial" })] })] })
      ]})
    ]
  })
];

// ── Actions Table ─────────────────────────────────────────────────────────────

const actionsTable = (rows) => new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [4200, 2880, 2280],
  rows: [
    new TableRow({
      tableHeader: true,
      children: [
        new TableCell({ borders, width: { size: 4200, type: WidthType.DXA },
          shading: { fill: BRAND_BLUE, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: "Action", bold: true, size: 20, font: "Arial", color: "FFFFFF" })] })] }),
        new TableCell({ borders, width: { size: 2880, type: WidthType.DXA },
          shading: { fill: BRAND_BLUE, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: "Source Signal", bold: true, size: 20, font: "Arial", color: "FFFFFF" })] })] }),
        new TableCell({ borders, width: { size: 2280, type: WidthType.DXA },
          shading: { fill: BRAND_BLUE, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: "Priority", bold: true, size: 20, font: "Arial", color: "FFFFFF" })] })] }),
      ]
    }),
    ...rows.map(([action, source, priority], i) =>
      new TableRow({ children: [
        new TableCell({ borders, width: { size: 4200, type: WidthType.DXA },
          shading: { fill: i % 2 === 0 ? "FFFFFF" : BRAND_LIGHT, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [body(action)] })] }),
        new TableCell({ borders, width: { size: 2880, type: WidthType.DXA },
          shading: { fill: i % 2 === 0 ? "FFFFFF" : BRAND_LIGHT, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [muted(source)] })] }),
        new TableCell({ borders, width: { size: 2280, type: WidthType.DXA },
          shading: { fill: i % 2 === 0 ? "FFFFFF" : BRAND_LIGHT, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: priority,
            bold: priority === "HIGH", size: 19, font: "Arial",
            color: priority === "HIGH" ? ACCENT : priority === "MEDIUM" ? "E67E22" : GRAY })] })] }),
      ]})
    )
  ]
});

// ── Document ──────────────────────────────────────────────────────────────────

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }]
    }]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial", color: BRAND_BLUE },
        paragraph: { spacing: { before: 320, after: 120 }, outlineLevel: 0 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            children: [
              new TextRun({ text: "CIVICOS INSTITUTE", bold: true, size: 20, font: "Arial", color: BRAND_BLUE }),
              new TextRun({ text: "\tBoard Intelligence Brief", size: 19, font: "Arial", color: GRAY }),
              new TextRun({ text: `\t${DATE}`, size: 19, font: "Arial", color: GRAY }),
            ],
            tabStops: [
              { type: TabStopType.CENTER, position: 4680 },
              { type: TabStopType.RIGHT, position: TabStopPosition.MAX }
            ],
            border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND_BLUE, space: 4 } }
          })
        ]
      })
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            children: [
              new TextRun({ text: "CONFIDENTIAL — CivicOS Institute Internal Use Only", size: 16, font: "Arial", color: GRAY, italics: true }),
              new TextRun({ text: "\tPage ", size: 16, font: "Arial", color: GRAY }),
              new TextRun({ children: [PageNumber.CURRENT], size: 16, font: "Arial", color: GRAY }),
            ],
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
            border: { top: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC", space: 4 } }
          })
        ]
      })
    },
    children: [

      // ── Title Block ──────────────────────────────────────────────────────────
      spacer(240, 80),
      new Paragraph({
        children: [new TextRun({ text: "Board Intelligence Brief", bold: true, size: 52, font: "Arial", color: BRAND_BLUE })],
        spacing: { before: 0, after: 80 }
      }),
      new Paragraph({
        children: [new TextRun({ text: DATE, size: 24, font: "Arial", color: GRAY })],
        spacing: { before: 0, after: 40 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "Automated institutional intelligence — prepared by Burt Prime", size: 19, font: "Arial", color: GRAY, italics: true })],
        spacing: { before: 0, after: 0 }
      }),
      rule(),

      // ── Executive Summary ────────────────────────────────────────────────────
      sectionHeader("Executive Summary"),
      bullet("Three high-priority signals this cycle: AI governance conflict (Anthropic/Pentagon), govtech commercialization pressure (Infocap), and civil-liberties/surveillance accountability risk (California ALPR network)."),
      bullet("Board priority this week: HIGH. Immediate action recommended on principles memo for acceptable-use boundaries in defense AI."),
      bullet("Website and analytics pipeline live; awaiting first real traffic data. CRM operational with hourly email sync active."),
      spacer(80, 0),
      rule(),

      // ── Signal Intelligence ──────────────────────────────────────────────────
      sectionHeader("Signal Intelligence"),
      new Paragraph({ children: [muted("3 board-ready signals this cycle · Source: Google Alerts + GNews · Scored by Qwen3.5-27B local inference")], spacing: { before: 0, after: 160 } }),

      ...signalCard(
        1,
        "Anthropic Rejects Pentagon Demand to Remove AI Safeguards",
        "NPR / Politico / Bloomberg / NYT",
        "https://www.npr.org/2026/02/26/nx-s1-5727847/anthropic-defense-hegseth-ai-weapons-surveillance",
        "CFR — The AI Sovereignty Paradox at Home and Abroad",
        "https://www.youtube.com/channel/UCL_A4jkwvKuMyToAPy3FQKQ",
        "Sets precedent for guardrails in defense AI. Anthropic is holding its acceptable-use policy against Pentagon pressure — the outcome defines the norm for all civic AI deployments.",
        "Risk: policy conflict could restrict AI tooling in government-adjacent civic work. Opportunity: CivicOS can lead on governance framing and publish a principled position memo.",
        "Draft a principles memo on acceptable-use boundaries for AI in defense and civic contexts."
      ),

      ...signalCard(
        2,
        "Infocap Launches MPVaaS, TRUST, and EASY for Government AI Modernization",
        "Citizen Times / Press Release",
        "https://www.citizen-times.com/press-release/story/63718/infocap-launches-mpvaas-trust-and-easy-to-accelerate-ai-driven-modernization-for-government-healthcare-programs/",
        null, null,
        "Vendor push into public-sector AI stack. Procurement hype cycle is accelerating in government healthcare and civic programs.",
        "Risk: organizations adopt unvetted AI tools under modernization pressure. Opportunity: CivicOS can publish an objective vendor evaluation rubric for civic AI procurement.",
        "Create a rapid vendor due-diligence checklist for civic AI procurement decisions."
      ),

      ...signalCard(
        3,
        "He Saw an Abandoned Trailer. Then He Uncovered a Surveillance Network on California's Border",
        "CalMatters",
        "https://calmatters.org/justice/2026/02/alpr-border-patrol-caltrans/",
        "Brookings Institution — Governance & Technology",
        "https://www.youtube.com/channel/UCi7jxgIOxcRaF4Q54U7lF3g",
        "Civil-liberties and accountability pressure is rising around surveillance infrastructure. 40+ license plate readers feeding data to federal agencies without public oversight.",
        "Risk: public trust erosion if civic organizations are silent. Opportunity: CivicOS can advance transparency and oversight standards work.",
        "Prepare oversight-focused briefing language on surveillance accountability for civic orgs."
      ),

      rule(),

      // ── Stakeholder Activity ─────────────────────────────────────────────────
      sectionHeader("Stakeholder Activity"),
      new Paragraph({ children: [muted("Source: CRM email sync · Past 7 days · Grant and giving-capacity contacts only")], spacing: { before: 0, after: 160 } }),
      bullet("CRM operational. Hourly email sync active as of February 27, 2026."),
      bullet("No grant or giving-capacity interactions logged this cycle — system came online today."),
      bullet("First CRM interaction data expected in tomorrow's brief as email pipeline matures."),
      spacer(80, 0),
      rule(),

      // ── Website & Reach ──────────────────────────────────────────────────────
      sectionHeader("Website & Reach"),
      new Paragraph({ children: [muted("Source: GA4 Property 526241272 · civicos-institute.org · Daily pull at 08:30")], spacing: { before: 0, after: 160 } }),
      bullet("GA4 analytics pipeline live as of February 27, 2026. Tag confirmed in global Jekyll layout."),
      bullet("Users: 0 · Sessions: 0 · Data collection active, awaiting first visitor traffic."),
      bullet("First meaningful analytics expected within 24–48 hours as site traffic begins flowing."),
      spacer(80, 0),
      rule(),

      // ── Recommended Actions ──────────────────────────────────────────────────
      sectionHeader("Recommended Actions"),
      spacer(0, 120),
      actionsTable([
        ["Draft principles memo on acceptable-use boundaries for AI in defense/civic contexts", "Anthropic / Pentagon signal", "HIGH"],
        ["Create vendor due-diligence checklist for civic AI procurement", "Infocap modernization launch", "HIGH"],
        ["Prepare oversight briefing language on surveillance accountability", "California ALPR network report", "HIGH"],
        ["Review first CRM interaction data when available (tomorrow's brief)", "CRM pipeline", "MEDIUM"],
        ["Share civicos-institute.org publicly to activate GA4 traffic data", "GA4 pipeline", "MEDIUM"],
        ["Sign off Qwen3.5 benchmark card to graduate model to default route", "Ops / Architecture", "MEDIUM"],
      ]),
      spacer(160, 0),
      rule(),

      // ── Footer Note ──────────────────────────────────────────────────────────
      new Paragraph({
        children: [muted("This brief is auto-compiled weekly every Monday at 07:00 by the CivicOS intelligence pipeline. Sources: Google Alerts, GNews, GovInfo RSS, YouTube channel monitoring. Inference: Qwen3.5-27B (local). Next brief: Monday, March 2, 2026.")],
        alignment: AlignmentType.CENTER,
        spacing: { before: 80, after: 0 }
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/sessions/serene-zealous-fermat/mnt/outputs/board_brief_2026-02-27.docx", buffer);
  console.log("✅ Board brief generated successfully.");
});
