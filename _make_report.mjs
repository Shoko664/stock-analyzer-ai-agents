// _make_report.mjs
// Generates a polished Word report from stock analysis JSON using the docx package.

import fs from "fs";
import {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, LevelFormat, PageNumber, Header, Footer,
  TabStopType, TabStopPosition,
} from "docx";

const [,, dataPath, outputPath] = process.argv;
const results = JSON.parse(fs.readFileSync(dataPath, "utf8"));

// ── Palette ───────────────────────────────────────────────────────────────────
const C = {
  navy:      "1B3A6B",
  blue:      "2563EB",
  lightBlue: "DBEAFE",
  green:     "16A34A",
  lightGreen:"DCFCE7",
  amber:     "D97706",
  lightAmber:"FEF3C7",
  red:       "DC2626",
  lightRed:  "FEE2E2",
  gray:      "6B7280",
  lightGray: "F3F4F6",
  white:     "FFFFFF",
};

const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "CBD5E1" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const NO_BORDER = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const NO_BORDERS = { top: NO_BORDER, bottom: NO_BORDER, left: NO_BORDER, right: NO_BORDER };

// ── Helpers ───────────────────────────────────────────────────────────────────

function scoreColor(score) {
  if (score >= 7) return C.green;
  if (score >= 5) return C.amber;
  return C.red;
}

function scoreBg(score) {
  if (score >= 7) return C.lightGreen;
  if (score >= 5) return C.lightAmber;
  return C.lightRed;
}

function para(text, opts = {}) {
  return new Paragraph({
    spacing: { before: opts.spaceBefore ?? 0, after: opts.spaceAfter ?? 120 },
    alignment: opts.align ?? AlignmentType.LEFT,
    children: [new TextRun({
      text,
      font: "Arial",
      size: opts.size ?? 22,
      bold: opts.bold ?? false,
      color: opts.color ?? "000000",
      italics: opts.italic ?? false,
    })],
  });
}

function spacer(pts = 160) {
  return new Paragraph({ spacing: { before: pts, after: 0 }, children: [] });
}

function sectionHeading(text) {
  return new Paragraph({
    spacing: { before: 280, after: 100 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: C.navy, space: 6 } },
    children: [new TextRun({ text, font: "Arial", size: 28, bold: true, color: C.navy })],
  });
}

function scoreCell(score, label) {
  const bg = scoreBg(score);
  const fg = scoreColor(score);
  return new TableCell({
    borders: NO_BORDERS,
    width: { size: 2200, type: WidthType.DXA },
    shading: { fill: bg, type: ShadingType.CLEAR },
    margins: { top: 120, bottom: 120, left: 160, right: 160 },
    verticalAlign: VerticalAlign.CENTER,
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 40 },
        children: [new TextRun({ text: `${score}/10`, font: "Arial", size: 36, bold: true, color: fg })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 0 },
        children: [new TextRun({ text: label, font: "Arial", size: 16, color: C.gray })],
      }),
    ],
  });
}

function labelCell(text, width = 2800) {
  return new TableCell({
    borders: BORDERS,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: C.lightGray, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [new TextRun({ text, font: "Arial", size: 20, bold: true, color: C.navy })] })],
  });
}

function valueCell(text, width = 6560) {
  return new TableCell({
    borders: BORDERS,
    width: { size: width, type: WidthType.DXA },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [new TextRun({ text: String(text ?? "N/A"), font: "Arial", size: 20 })] })],
  });
}

function fmtNum(val, suffix = "", multiplier = 1, decimals = 1) {
  if (val == null) return "N/A";
  return `${(val * multiplier).toFixed(decimals)}${suffix}`;
}

// ── Build one ticker section ──────────────────────────────────────────────────

function buildTickerSection(r) {
  const f = r.fundamentals;
  const nodes = [];

  // Company header bar
  nodes.push(new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [7160, 2200],
    rows: [new TableRow({ children: [
      new TableCell({
        borders: NO_BORDERS,
        width: { size: 7160, type: WidthType.DXA },
        shading: { fill: C.navy, type: ShadingType.CLEAR },
        margins: { top: 160, bottom: 160, left: 240, right: 120 },
        verticalAlign: VerticalAlign.CENTER,
        children: [
          new Paragraph({ spacing: { before: 0, after: 40 }, children: [
            new TextRun({ text: r.company_name, font: "Arial", size: 36, bold: true, color: C.white }),
            new TextRun({ text: `  (${r.ticker})`, font: "Arial", size: 24, color: "93C5FD" }),
          ]}),
          new Paragraph({ spacing: { before: 0, after: 0 }, children: [
            new TextRun({ text: `Analysis date: ${r.date.split("T")[0]}`, font: "Arial", size: 18, color: "CBD5E1" }),
          ]}),
        ],
      }),
      new TableCell({
        borders: NO_BORDERS,
        width: { size: 2200, type: WidthType.DXA },
        shading: { fill: scoreColor(Math.round(r.composite)) >= C.green ? C.green : r.composite >= 5 ? C.amber : C.red, type: ShadingType.CLEAR },
        margins: { top: 160, bottom: 160, left: 120, right: 120 },
        verticalAlign: VerticalAlign.CENTER,
        children: [
          new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 40 }, children: [
            new TextRun({ text: `${r.composite}`, font: "Arial", size: 52, bold: true, color: C.white }),
          ]}),
          new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 0 }, children: [
            new TextRun({ text: "COMPOSITE", font: "Arial", size: 14, color: "E0E7FF", bold: true }),
          ]}),
        ],
      }),
    ]})],
  }));

  nodes.push(spacer(120));

  // Agent score cards (3 cells)
  nodes.push(new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [3120, 3120, 3120],
    rows: [new TableRow({ children: [
      scoreCell(r.fund_score,  "Fundamentals"),
      scoreCell(r.sent_score,  "Sentiment"),
      scoreCell(r.val_score,   "Valuation"),
    ]})],
  }));

  nodes.push(spacer(80));

  // Justification table
  const agentRows = [
    ["Agent A – Fundamentals", r.fund_just],
    ["Agent B – Sentiment",    r.sent_just],
    ["Agent C – Valuation",    r.val_just],
  ];
  nodes.push(new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [2800, 6560],
    rows: agentRows.map(([label, val]) => new TableRow({ children: [labelCell(label), valueCell(val)] })),
  }));

  nodes.push(spacer(100));

  // Risk flags
  if (r.risk_flags && r.risk_flags.length > 0) {
    nodes.push(new Paragraph({
      spacing: { before: 0, after: 60 },
      children: [new TextRun({ text: "⚑  Risk Flags: ", font: "Arial", size: 20, bold: true, color: C.red })],
    }));
    r.risk_flags.forEach(flag => {
      nodes.push(new Paragraph({
        spacing: { before: 0, after: 60 },
        children: [
          new TextRun({ text: "  •  ", font: "Arial", size: 20 }),
          new TextRun({ text: flag, font: "Arial", size: 20, color: C.red }),
        ],
      }));
    });
    nodes.push(spacer(60));
  }

  // Verdict
  nodes.push(new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [new TableRow({ children: [new TableCell({
      borders: NO_BORDERS,
      width: { size: 9360, type: WidthType.DXA },
      shading: { fill: r.composite >= 7 ? C.lightGreen : r.composite >= 5 ? C.lightAmber : C.lightRed, type: ShadingType.CLEAR },
      margins: { top: 100, bottom: 100, left: 160, right: 160 },
      children: [new Paragraph({ children: [
        new TextRun({ text: r.verdict, font: "Arial", size: 22, bold: true,
          color: r.composite >= 7 ? C.green : r.composite >= 5 ? C.amber : C.red }),
      ]})],
    })]})],
  }));

  nodes.push(spacer(80));

  // Fundamentals metrics table
  nodes.push(sectionHeading("Financial Metrics"));
  const metrics = [
    ["Trailing P/E",     fmtNum(f.trailing_pe,    "x")],
    ["Forward P/E",      fmtNum(f.forward_pe,     "x")],
    ["Profit Margin",    fmtNum(f.profit_margin,  "%", 100)],
    ["Revenue Growth",   fmtNum(f.revenue_growth, "%", 100)],
    ["Debt / Equity",    fmtNum(f.debt_to_equity, "", 1)],
    ["Return on Equity", fmtNum(f.return_on_equity, "%", 100)],
    ["Free Cash Flow",   f.free_cashflow != null
      ? `$${(f.free_cashflow / 1e9).toFixed(2)}B` : "N/A"],
    ["Market Cap",       f.market_cap != null
      ? `$${(f.market_cap / 1e9).toFixed(1)}B` : "N/A"],
  ];
  nodes.push(new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [2800, 6560],
    rows: metrics.map(([label, val]) => new TableRow({ children: [labelCell(label), valueCell(val)] })),
  }));

  nodes.push(spacer(80));

  // Headlines
  if (r.headlines && r.headlines.length > 0) {
    nodes.push(sectionHeading("Recent Headlines"));
    r.headlines.forEach((h, i) => {
      nodes.push(new Paragraph({
        spacing: { before: 60, after: 60 },
        children: [
          new TextRun({ text: `${i + 1}.  `, font: "Arial", size: 20, bold: true, color: C.blue }),
          new TextRun({ text: h, font: "Arial", size: 20, color: "374151" }),
        ],
      }));
    });
  }

  nodes.push(spacer(300));
  return nodes;
}

// ── Summary table across all tickers ─────────────────────────────────────────

function buildSummaryTable(results) {
  const headerRow = new TableRow({ children: [
    ["Ticker", 1560], ["Company", 3400], ["Fund.", 1100], ["Sent.", 1100], ["Val.", 1100], ["Composite", 1100]
  ].map(([text, width]) => new TableCell({
    borders: BORDERS,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: C.navy, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text, font: "Arial", size: 18, bold: true, color: C.white })
    ]})],
  }))});

  const dataRows = results.map(r => {
    const cols = [
      [r.ticker,          1560, true],
      [r.company_name,    3400, false],
      [`${r.fund_score}/10`,  1100, true],
      [`${r.sent_score}/10`,  1100, true],
      [`${r.val_score}/10`,   1100, true],
      [`${r.composite}/10`,   1100, true],
    ];
    return new TableRow({ children: cols.map(([text, width, center]) => new TableCell({
      borders: BORDERS,
      width: { size: width, type: WidthType.DXA },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [new Paragraph({
        alignment: center ? AlignmentType.CENTER : AlignmentType.LEFT,
        children: [new TextRun({ text: String(text), font: "Arial", size: 20 })],
      })],
    }))});
  });

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [1560, 3400, 1100, 1100, 1100, 1100],
    rows: [headerRow, ...dataRows],
  });
}

// ── Assemble document ─────────────────────────────────────────────────────────

const dateStr = new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });

const children = [
  // Cover title
  new Paragraph({
    spacing: { before: 720, after: 120 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Stock Analysis Report", font: "Arial", size: 56, bold: true, color: C.navy })],
  }),
  new Paragraph({
    spacing: { before: 0, after: 80 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: dateStr, font: "Arial", size: 24, color: C.gray })],
  }),
  new Paragraph({
    spacing: { before: 0, after: 80 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: `Tickers analyzed: ${results.map(r => r.ticker).join("  •  ")}`,
      font: "Arial", size: 22, color: C.blue, bold: true,
    })],
  }),
  spacer(160),

  // Executive summary table
  new Paragraph({ spacing: { before: 0, after: 100 }, children: [
    new TextRun({ text: "Executive Summary", font: "Arial", size: 32, bold: true, color: C.navy }),
  ]}),
  buildSummaryTable(results),
  spacer(200),

  // Individual ticker sections
  ...results.flatMap(buildTickerSection),

  // Disclaimer
  new Paragraph({
    spacing: { before: 200, after: 60 },
    border: { top: { style: BorderStyle.SINGLE, size: 4, color: C.lightGray, space: 8 } },
    children: [new TextRun({ text: "Disclaimer", font: "Arial", size: 18, bold: true, color: C.gray })],
  }),
  para(
    "This report is generated by AI agents for informational purposes only and does not constitute financial advice. " +
    "Always conduct your own due diligence before making investment decisions.",
    { size: 18, color: C.gray, italic: true }
  ),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
      },
    },
    headers: {
      default: new Header({ children: [
        new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.navy, space: 4 } },
          children: [new TextRun({ text: "Stock Analysis Report  |  Confidential", font: "Arial", size: 18, color: C.gray })],
        }),
      ]}),
    },
    footers: {
      default: new Footer({ children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: C.lightGray, space: 4 } },
          children: [
            new TextRun({ text: "Page ", font: "Arial", size: 18, color: C.gray }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: C.gray }),
          ],
        }),
      ]}),
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outputPath, buf);
  console.log(`Report written: ${outputPath}`);
});
