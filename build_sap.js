const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel, BorderStyle,
  WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak,
  TabStopType, TabStopPosition
} = require('docx');
const fs = require('fs');

// ─── Colour palette ───────────────────────────────────────────────────────────
const NAVY   = "1F3864";
const BLUE   = "2E75B6";
const LGRAY  = "F2F2F2";
const MGRAY  = "D9D9D9";
const WHITE  = "FFFFFF";
const BLACK  = "000000";

// ─── Border helpers ───────────────────────────────────────────────────────────
const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" };
const allBorders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const noBorder   = { style: BorderStyle.NONE };
const noBorders  = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

// ─── Paragraph helpers ────────────────────────────────────────────────────────
const p = (text, opts = {}) => new Paragraph({
  children: [new TextRun({ text, font: "Arial", size: opts.size || 22,
    bold: opts.bold || false, italics: opts.italic || false,
    color: opts.color || BLACK })],
  spacing: { before: opts.before || 80, after: opts.after || 80 },
  alignment: opts.align || AlignmentType.LEFT,
});

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text, font: "Arial", size: 28, bold: true, color: WHITE })],
  shading: { fill: NAVY, type: ShadingType.CLEAR },
  spacing: { before: 280, after: 160 },
  indent: { left: 120 },
});

const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text, font: "Arial", size: 24, bold: true, color: NAVY })],
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLUE } },
  spacing: { before: 240, after: 120 },
});

const h3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  children: [new TextRun({ text, font: "Arial", size: 22, bold: true, color: BLUE })],
  spacing: { before: 180, after: 80 },
});

const bullet = (text, lvl = 0) => new Paragraph({
  numbering: { reference: "bullets", level: lvl },
  children: [new TextRun({ text, font: "Arial", size: 21 })],
  spacing: { before: 40, after: 40 },
});

const num = (text, lvl = 0) => new Paragraph({
  numbering: { reference: "numbers", level: lvl },
  children: [new TextRun({ text, font: "Arial", size: 21 })],
  spacing: { before: 40, after: 40 },
});

const note = (text) => new Paragraph({
  children: [new TextRun({ text: "NOTE: " + text, font: "Arial", size: 20,
    italics: true, color: "555555" })],
  indent: { left: 360 },
  spacing: { before: 60, after: 60 },
});

const blank = () => new Paragraph({ children: [new TextRun("")], spacing: { before: 60, after: 60 } });

// ─── Table helpers ────────────────────────────────────────────────────────────
const W = 9360; // content width (US Letter 1" margins)

const hdrCell = (text, w, span = 1) => new TableCell({
  borders: allBorders,
  width: { size: w, type: WidthType.DXA },
  shading: { fill: NAVY, type: ShadingType.CLEAR },
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  columnSpan: span,
  children: [new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 20, bold: true, color: WHITE })],
    alignment: AlignmentType.CENTER,
  })],
});

const subHdrCell = (text, w) => new TableCell({
  borders: allBorders,
  width: { size: w, type: WidthType.DXA },
  shading: { fill: BLUE, type: ShadingType.CLEAR },
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  children: [new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 20, bold: true, color: WHITE })],
    alignment: AlignmentType.CENTER,
  })],
});

const dataCell = (text, w, shade = false, bold = false) => new TableCell({
  borders: allBorders,
  width: { size: w, type: WidthType.DXA },
  shading: { fill: shade ? LGRAY : WHITE, type: ShadingType.CLEAR },
  margins: { top: 60, bottom: 60, left: 120, right: 120 },
  children: [new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 20, bold, color: BLACK })],
  })],
});

// ─── Title page ───────────────────────────────────────────────────────────────
const titlePage = () => [
  new Paragraph({ spacing: { before: 1440 } }),
  new Paragraph({
    children: [new TextRun({ text: "STATISTICAL ANALYSIS PLAN", font: "Arial", size: 48, bold: true, color: NAVY })],
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 240 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Study EFC6193 / TROPIC Trial", font: "Arial", size: 32, bold: true, color: BLUE })],
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 160 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "A Randomized, Open-Label, Multi-Center Phase III Study of", font: "Arial", size: 24, color: "444444" })],
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 60 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Cabazitaxel + Prednisone vs. Mitoxantrone + Prednisone", font: "Arial", size: 24, bold: true, color: "444444" })],
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 60 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "in Hormone-Refractory Metastatic Prostate Cancer", font: "Arial", size: 24, color: "444444" })],
    alignment: AlignmentType.CENTER, spacing: { before: 0, after: 480 },
  }),

  // Metadata box
  new Table({
    width: { size: 6480, type: WidthType.DXA },
    float: { horizontalAnchor: "text", absoluteHorizontalPosition: 1440 },
    rows: [
      new TableRow({ children: [hdrCell("DOCUMENT INFORMATION", 6480)] }),
      new TableRow({ children: [
        dataCell("SAP Version", 2160, true, true),
        dataCell("1.0", 4320, false),
      ]}),
      new TableRow({ children: [
        dataCell("SAP Date", 2160, true, true),
        dataCell("2026-05-24 (Updated to reflect current 2026 regulatory framework)", 4320, false),
      ]}),
      new TableRow({ children: [
        dataCell("Protocol Version", 2160, true, true),
        dataCell("Amendment 5 (21-Jul-2008)", 4320, false),
      ]}),
      new TableRow({ children: [
        dataCell("ADaMIG Version", 2160, true, true),
        dataCell("1.3 (mandatory FDA standard from 2024-03-15)", 4320, false),
      ]}),
      new TableRow({ children: [
        dataCell("Data Source", 2160, true, true),
        dataCell("Project Data Sphere — Sanofi US contribution", 4320, false),
      ]}),
      new TableRow({ children: [
        dataCell("Authorization", 2160, true, true),
        dataCell("PDS Terms of Use. De-identified per HIPAA. No IRB required.", 4320, false),
      ]}),
      new TableRow({ children: [
        dataCell("Authored By", 2160, true, true),
        dataCell("[Programmer Name] — Secondary Analysis, Portfolio Project", 4320, false),
      ]}),
      new TableRow({ children: [
        dataCell("Validation Target", 2160, true, true),
        dataCell("Lancet 2010;376:1147-54. Median OS: CbzP 15.1 mo vs MP 12.7 mo; HR=0.70", 4320, false),
      ]}),
    ],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ─── SECTION 1 ────────────────────────────────────────────────────────────────
const section1 = () => [
  h1("1  STUDY OVERVIEW"),
  blank(),
  h2("1.1  Background and Rationale"),
  p("Cabazitaxel (XRP6258) is a semi-synthetic taxane developed by Sanofi with minimal recognition by the P-glycoprotein multidrug resistance mechanism. TROPIC (EFC6193) was a Phase III, randomized, open-label, multi-center trial enrolling 755 patients across 146 centers in 26 countries. The trial demonstrated superior overall survival of cabazitaxel plus prednisone versus mitoxantrone plus prednisone in men with mCRPC previously treated with docetaxel (de Bono et al., Lancet 2010)."),
  blank(),
  p("This Statistical Analysis Plan governs a secondary analysis of the TROPIC data obtained from Project Data Sphere (PDS). The source data constitute the complete patient-level SDTM dataset contributed by Sanofi US to PDS. This SAP is authored independently and does not represent Sanofi's original SAP, which is proprietary and unpublished."),
  blank(),
  h2("1.2  Study Design"),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2160, 7200],
    rows: [
      new TableRow({ children: [hdrCell("Parameter", 2160), hdrCell("Description", 7200)] }),
      ...[
        ["Study Number", "EFC6193 / XRP6258"],
        ["Study Name", "TROPIC"],
        ["Phase", "III"],
        ["Design", "Randomized, open-label, active-controlled, multi-center, multinational"],
        ["Indication", "Hormone-refractory (castration-resistant) metastatic prostate cancer (mCRPC)"],
        ["Randomization", "1:1; IVRS; stratified by ECOG PS (0-1 vs 2) and measurability of disease (RECIST measurable vs non-measurable)"],
        ["Arm A (Control)", "Mitoxantrone 12 mg/m\u00B2 IV Day 1 q3w + Prednisone 10 mg/day oral"],
        ["Arm B (Experimental)", "Cabazitaxel 25 mg/m\u00B2 IV Day 1 q3w + Prednisone 10 mg/day oral"],
        ["Cycle Length", "21 days (3 weeks). Maximum 10 cycles."],
        ["Follow-up", "Until death or maximum 2 years (104 weeks)"],
        ["Sample Size", "755 randomized (Arm A n=377, Arm B n=378); target 511 deaths for primary analysis"],
        ["Data Cut-off", "2010-03-10"],
        ["SDTM Standard", "SDTM-IG 3.1.1 (source). ADaM built to ADaMIG v1.3."],
      ].map(([k, v], i) => new TableRow({
        children: [dataCell(k, 2160, true, true), dataCell(v, 7200, i % 2 === 0)],
      })),
    ],
  }),
  blank(),
  h2("1.3  Important Source Data Notes"),
  p("The following characteristics of the source SDTM data are non-standard relative to current SDTM-IG 3.4 and must be documented in the Study Data Reviewer's Guide (SDRG):", { bold: false }),
  blank(),
  bullet("AE dates are stored as AESTWK/AEENWK (integer weeks from first dose), not ISO 8601 DTC variables. Conversion to AESTDTC/AEENDTC is required before ADaM derivation. Algorithm: AESTDTC = RFSTDTC + (AESTWK - 1) \u00D7 7 days."),
  bullet("SUPPEX contains Sanofi pre-computed exposure variables (EXCUMD2, EXTRINT, EXDELAY) that serve as validation targets for ADEX derivations."),
  bullet("SUPPDM contains pre-computed population flags (ITT, SAFETY, PPROT) and baseline BSA (BSABL)."),
  bullet("LB.LBTOXGR contains CTCAE v3.0 grades assigned by Sanofi. These are used as the primary source for ATOXGR in ADLB. ADaM derivations independently verify against protocol NCI CTCAE v3.0 thresholds."),
  bullet("PN domain contains pain intensity (PPI) and analgesic score data — a non-standard SDTM domain created by Sanofi specifically for this trial."),
  bullet("LS domain contains individual lesion measurements for RECIST derivation."),
  new Paragraph({ children: [new PageBreak()] }),
];

// ─── SECTION 2 ────────────────────────────────────────────────────────────────
const section2 = () => [
  h1("2  STUDY OBJECTIVES AND ENDPOINTS"),
  blank(),
  h2("2.1  Primary Objective"),
  p("To determine whether cabazitaxel plus prednisone (CbzP) improves Overall Survival (OS) compared to mitoxantrone plus prednisone (MP) in patients with mCRPC previously treated with a docetaxel-containing regimen."),
  blank(),
  h2("2.2  Secondary Objectives"),
  num("To compare PSA response rates between treatment arms."),
  num("To compare PSA progression-free rates between treatment arms."),
  num("To compare Progression-Free Survival (PFS) — composite of tumor, PSA, or pain progression, or death."),
  num("To compare Overall Response Rate (ORR) in the measurable disease subpopulation."),
  num("To compare pain response rates in patients with baseline pain."),
  num("To compare pain progression between treatment arms."),
  num("To characterize the safety and tolerability of cabazitaxel plus prednisone."),
  blank(),
  h2("2.3  Exploratory Objectives (Secondary Analysis Additions)"),
  num("To characterize cabazitaxel dose exposure (RDI, cumulative dose) and its relationship to hematologic toxicity (ANC nadir, recovery latency) per FDA Project Optimus dose-optimization framework."),
  num("To evaluate the exposure-response relationship between relative dose intensity and Grade \u22653 neutropenia stratified by G-CSF prophylactic use."),
  num("To construct a benefit-risk summary comparing OS benefit versus Grade \u22653 toxicity rates by relative dose intensity tertile."),
  num("To assess OS and PFS within pre-specified prognostic subgroups (ECOG PS, measurable disease, visceral metastases, baseline PSA, ALP, albumin, age, docetaxel progression timing)."),
  blank(),
  h2("2.4  Endpoints Summary Table"),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [1560, 2200, 3200, 2400],
    rows: [
      new TableRow({ children: [hdrCell("Type", 1560), hdrCell("Endpoint", 2200), hdrCell("Definition", 3200), hdrCell("ADaM Dataset", 2400)] }),
      ...[
        ["Primary","Overall Survival (OS)","Time from randomization to death, any cause. Censor at last known alive date or cut-off, whichever first.","ADTTE (PARAMCD=OS)"],
        ["Secondary","PSA Response","PSA decline \u226550% from baseline, confirmed \u22653 weeks later. Applies to patients with baseline PSA \u226520 ng/mL.","ADLB (PARAMCD=PSAD50)"],
        ["Secondary","PSA Progression","Non-responders: \u226525% rise over nadir + absolute \u22655 ng/mL confirmed \u22651 week. Responders: \u226550% rise over nadir + \u22655 ng/mL confirmed.","ADRS (PARAMCD=PSPROG)"],
        ["Secondary","PFS (composite)","Time from randomization to first of: RECIST tumor PD, PSA progression, pain progression (with clinical/radiological support), or death.","ADTTE (PARAMCD=PFS)"],
        ["Secondary","ORR","Proportion of CR+PR per RECIST in measurable disease subset, confirmed \u22654 weeks after first response.","ADRS (PARAMCD=OBJRESP)"],
        ["Secondary","Pain Response","In patients with baseline PPI \u22652 or mean AS \u226510: 2-point PPI reduction with no AS increase OR 50% AS reduction with no pain increase, maintained for 2 consecutive visits \u22653 weeks apart.","ADRS derived from PN domain"],
        ["Secondary","Pain Progression","\u22651 point PPI increase from nadir on 2 consecutive visits \u22653 weeks apart OR \u226525% AS increase from baseline on 2 consecutive visits OR palliative radiotherapy.","ADTTE (PARAMCD=TTPAIN)"],
        ["Safety","TEAEs","Treatment-emergent: first occurrence or worsening on/after Day 1 of dosing through 30 days post last dose. Graded per NCI CTCAE v3.0.","ADAE"],
        ["Exploratory","ANC Nadir + Recovery","Min ANC per cycle; days from nadir to ANC \u22651500/mm\u00B3. G-CSF stratified.","ADLB (PARAMCD=ANCNADIR, ANCRECDY)"],
        ["Exploratory","Relative Dose Intensity","(Actual dose intensity / Planned dose intensity) \u00D7 100%.","ADEX (PARAMCD=RDI)"],
        ["Exploratory","Exposure-Response","RDI vs ANC nadir scatter + regression. Optimus benefit-risk by RDI tertile.","ADEX + ADLB + ADAE + ADTTE"],
      ].map(([t, e, d, ds], i) => new TableRow({
        children: [dataCell(t, 1560, i%2===0, t==="Primary"), dataCell(e, 2200, i%2===0), dataCell(d, 3200, i%2===0), dataCell(ds, 2400, i%2===0)],
      })),
    ],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ─── SECTION 3 ────────────────────────────────────────────────────────────────
const section3 = () => [
  h1("3  ANALYSIS POPULATIONS"),
  blank(),
  h2("3.1  Intent-to-Treat (ITT) Population"),
  p("All randomized patients regardless of whether they received any study drug or received a different treatment than assigned. This is the primary population for all efficacy analyses. Treatment comparisons use the randomized arm, not the actual arm received."),
  p("ADaM variable: ADSL.ITTFL = 'Y'. Source: SUPPDM.QNAM='ITT' / QVAL='Y'. Validate: should equal all records in DM domain.", { italic: true }),
  blank(),
  h2("3.2  Safety Population (All-Treated, AT)"),
  p("All patients who received at least one partial dose of any study drug. This is the denominator for all safety analyses. Treatment group assignment based on treatment actually received, not randomized arm."),
  p("ADaM variable: ADSL.SAFFL = 'Y'. Source: SUPPDM.QNAM='SAFETY'. Validate: should equal all subjects with \u22651 EX record.", { italic: true }),
  blank(),
  h2("3.3  Per-Protocol Population"),
  p("All ITT patients without major protocol deviations. Used for sensitivity analyses of efficacy endpoints. Definition of major deviations: missing \u22652 consecutive tumor assessments without documented progression; received prohibited concomitant anti-cancer therapy during treatment phase; enrolled despite not meeting key inclusion/exclusion criteria."),
  p("ADaM variable: ADSL.PPROTFL = 'Y'. Source: SUPPDM.QNAM='PPROT'.", { italic: true }),
  blank(),
  h2("3.4  Population Sizes (Expected)"),
  new Table({
    width: { size: 6000, type: WidthType.DXA },
    columnWidths: [2400, 1200, 1200, 1200],
    rows: [
      new TableRow({ children: [hdrCell("Population", 2400), hdrCell("Overall", 1200), hdrCell("CbzP", 1200), hdrCell("MP", 1200)] }),
      ...[
        ["Randomized (ITT)", "755", "378", "377"],
        ["Safety (AT)", "\u2248755", "\u2248378", "\u2248377"],
        ["Per-Protocol", "TBD", "TBD", "TBD"],
        ["Measurable Disease Subset", "\u2248390", "TBD", "TBD"],
        ["Baseline Pain Subset (PPI\u22652 or AS\u226510)", "TBD", "TBD", "TBD"],
        ["Baseline PSA \u226520 ng/mL (PSA response)", "TBD", "TBD", "TBD"],
      ].map(([pop, all, cbz, mp], i) => new TableRow({
        children: [dataCell(pop, 2400, i%2===0, i===0), dataCell(all, 1200, i%2===0), dataCell(cbz, 1200, i%2===0), dataCell(mp, 1200, i%2===0)],
      })),
    ],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ─── SECTION 4 ────────────────────────────────────────────────────────────────
const section4 = () => [
  h1("4  STATISTICAL METHODS"),
  blank(),
  h2("4.1  Primary Endpoint — Overall Survival"),
  h3("4.1.1  Test Procedure"),
  p("Primary analysis: stratified log-rank test comparing OS between CbzP and MP in the ITT population. Stratification factors as used in randomization IVRS:"),
  bullet("Measurability of disease per RECIST (measurable vs. non-measurable)"),
  bullet("ECOG Performance Status (0-1 vs. 2)"),
  blank(),
  p("SAS: PROC LIFETEST with STRATA statement. R: survival::survdiff() with strata()."),
  blank(),
  h3("4.1.2  Significance Level and Multiplicity"),
  p("This is a secondary analysis of a completed trial. The original O'Brien-Fleming alpha-spending was: IA2 = 0.0076 (two-sided), Final = 0.0476 (two-sided). For this independent re-analysis, the conventional 2-sided alpha = 0.05 is applied to all formal tests, with hierarchical gatekeeping across secondary endpoints:"),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [720, 3240, 2160, 3240],
    rows: [
      new TableRow({ children: [hdrCell("Step", 720), hdrCell("Endpoint", 3240), hdrCell("Alpha", 2160), hdrCell("Gate Rule", 3240)] }),
      ...[
        ["1","Overall Survival (Primary)","0.05 (2-sided)","Must be significant to proceed to Step 2"],
        ["2","Progression-Free Survival","0.05 (2-sided)","Tested only if Step 1 significant"],
        ["3","PSA Response Rate","0.05 (2-sided)","Tested only if Step 2 significant"],
        ["4","ORR (measurable disease)","0.05 (2-sided)","Tested only if Step 3 significant"],
        ["—","All other endpoints","Exploratory","No alpha protection; descriptive only"],
      ].map(([s,e,a,g], i) => new TableRow({
        children: [dataCell(s,720,i%2===0,i===0), dataCell(e,3240,i%2===0), dataCell(a,2160,i%2===0), dataCell(g,3240,i%2===0)],
      })),
    ],
  }),
  blank(),
  h3("4.1.3  Kaplan-Meier Estimation"),
  p("KM survival curves estimated per arm. Median OS with 95% CI using the Brookmeyer-Crowley (1982) method. KM curves presented with number-at-risk table at 3-month intervals below the x-axis. SAS: PROC LIFETEST. R: survival::survfit() + survminer::ggsurvplot()."),
  blank(),
  h3("4.1.4  Hazard Ratio Estimation"),
  p("Cox proportional hazards model stratified by the same two stratification factors. Report: HR, 95% CI, and p-value. Assumption testing: Schoenfeld residuals plot and log-log survival curve. SAS: PROC PHREG with STRATA statement. R: survival::coxph()."),
  blank(),
  h3("4.1.5  OS Censoring Rules"),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [3600, 3120, 2640],
    rows: [
      new TableRow({ children: [hdrCell("Scenario", 3600), hdrCell("CNSR Value", 3120), hdrCell("Date Used (ADTM)", 2640)] }),
      ...[
        ["Death confirmed during study or follow-up","0 (Event)","ADSL.DTHDT"],
        ["No death: last known alive date","1 (Censored)","ADSL.LSTALVDT"],
        ["Loss to follow-up: last contact date","1 (Censored)","max(SV.SVSTDTC, VS.VSDTC) per subject"],
        ["Administrative cut-off only","1 (Censored)","Data cut-off: 2010-03-10"],
      ].map(([s,c,d], i) => new TableRow({
        children: [dataCell(s,3600,i%2===0), dataCell(c,3120,i%2===0), dataCell(d,2640,i%2===0)],
      })),
    ],
  }),
  blank(),
  h3("4.1.6  OS Sensitivity Analyses"),
  p("Two pre-specified sensitivity analyses supplement the primary Cox PH analysis:"),
  bullet("Restricted Mean Survival Time (RMST) at \u03C4 = 12 months: accounts for potential non-proportional hazards. RMST difference (CbzP minus MP) with 95% CI and p-value. SAS: PROC LIFETEST RMST=(365.25). R: survRM2::rmst2(). The \u03C4 = 12 months is pre-specified; sensitivity to alternative \u03C4 values (18 and 24 months) reported in appendix."),
  bullet("Landmark analysis at 6 and 12 months: proportion of subjects surviving beyond each landmark, comparing arms by chi-square test. Restricts to subjects event-free at the landmark."),
  blank(),
  h2("4.2  Secondary Endpoint — Progression-Free Survival"),
  h3("4.2.1  PFS Definition (Composite Endpoint)"),
  p("PFS = time from randomization to first occurrence of any of:"),
  bullet("Radiological tumor progression per RECIST (confirmed: \u226520% increase in sum of target lesion diameters OR new lesion)"),
  bullet("PSA progression (per Section 4.4 definition, with clinical/radiological evidence support — pain progression alone without clinical evidence does not count for PFS)"),
  bullet("Pain progression (supported by clinical and/or radiological evidence of disease progression — per protocol Section 9.1.2.4)"),
  bullet("Death from any cause"),
  blank(),
  note("Pain progression as a PFS event component requires corroborating clinical or radiological evidence of disease progression per protocol. Isolated pain score changes without disease evidence are NOT counted as PFS events."),
  blank(),
  h3("4.2.2  PFS Censoring Hierarchy"),
  p("Applied in the following priority order (first applicable rule wins):"),
  num("Documented progression date if event occurred and no administrative issues."),
  num("Last evaluable tumor assessment date if missing-to-progression rule applies (no post-baseline assessment available)."),
  num("NACTDT - 1 day: if new anti-cancer therapy started before documented progression (ADCM.NACTDT)."),
  num("Date of last radiological assessment."),
  num("ADSL.LSTALVDT if no tumor assessments were performed."),
  blank(),
  h3("4.2.3  PFS Statistical Methods"),
  p("Same as OS: stratified log-rank test, stratified Cox PH model (HR + 95% CI), KM curves. Sensitivity: ANL02FL-based analysis excluding assessments performed after new anti-cancer therapy (NACTDT)."),
  blank(),
  h2("4.3  Secondary Endpoint — PSA Response"),
  h3("4.3.1  Eligible Population"),
  p("Patients with baseline PSA \u226520 ng/mL (ADSL.PSABL \u226520). Denominator = number of PSA-evaluable patients in this subset per arm."),
  blank(),
  h3("4.3.2  Response Definition"),
  p("PSA decline of \u226550% from baseline (PCHG \u2264 -50) confirmed by a second PSA measurement at least 3 weeks (\u226521 days) later also meeting the \u226550% criterion. Both measurements compared against the baseline value."),
  p("ADaM derivation: ADLB where PARAMCD='PSAD50'. AVALC = 'Y' when confirmed, 'N' otherwise.", { italic: true }),
  blank(),
  h3("4.3.3  Statistical Test"),
  p("Chi-square test comparing proportions of PSA responders between arms. Report n/N (%), 95% Clopper-Pearson CI per arm, and p-value. Fisher's exact test if any cell expected count < 5. SAS: PROC FREQ with CHISQ option. R: prop.test() or fisher.test()."),
  blank(),
  h2("4.4  Secondary Endpoint — PSA Progression"),
  h3("4.4.1  Differential Definition by PSA Response Status"),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [3120, 6240],
    rows: [
      new TableRow({ children: [hdrCell("Patient Category", 3120), hdrCell("PSA Progression Definition", 6240)] }),
      ...[
        ["PSA Non-Responders (PSAD50='N')","PSA rise \u226525% above nadir AND absolute increase \u22655 ng/mL above nadir, confirmed by second value \u22651 week later."],
        ["PSA Responders (PSAD50='Y') and non-evaluable at baseline","PSA rise \u226550% above nadir AND absolute increase \u22655 ng/mL above nadir, confirmed by second value \u22651 week later."],
      ].map(([c,d],i) => new TableRow({
        children: [dataCell(c,3120,i%2===0,true), dataCell(d,6240,i%2===0)],
      })),
    ],
  }),
  blank(),
  h3("4.4.2  Statistical Methods"),
  p("Time to PSA Progression: KM curves, log-rank test, Cox PH model with same stratification factors. Median + 95% CI (Brookmeyer-Crowley)."),
  blank(),
  h2("4.5  Secondary Endpoint — ORR (Measurable Disease Subset)"),
  p("Proportion of confirmed CR + PR per RECIST in the ITT measurable disease subset (ADSL.MEASDISFL='Y'). Confirmation required: repeat imaging \u22654 weeks after first documentation. Overall response categories: CR, PR, SD, PD, NE (not evaluable). Chi-square test comparing responder proportions. ORR = (CR + PR) / N evaluable \u00D7 100."),
  blank(),
  h2("4.6  Secondary Endpoints — Pain Response and Pain Progression"),
  h3("4.6.1  Eligible Population for Pain Response"),
  p("Patients with baseline median PPI \u22652 (McGill-Melzack) OR mean Analgesic Score (AS) \u226510 (morphine equivalents per protocol Appendix G). Flag: ADSL.PAINBL = 'Y'."),
  blank(),
  h3("4.6.2  Pain Response Definition (Either Criterion)"),
  bullet("Criterion 1: \u22652-point reduction from baseline median PPI with NO concomitant increase in analgesic score, maintained for 2 consecutive visits \u22653 weeks apart."),
  bullet("Criterion 2 (only in patients with baseline mean AS \u226510): \u226550% reduction in AS from baseline with NO concomitant increase in pain, maintained for 2 consecutive visits \u22653 weeks apart."),
  blank(),
  h3("4.6.3  Pain Progression Definition (Any Criterion)"),
  bullet("\u22651-point PPI increase from PPI nadir on 2 consecutive visits \u22653 weeks apart, OR"),
  bullet("\u226525% increase in mean AS from baseline score on 2 consecutive visits \u22653 weeks apart, OR"),
  bullet("Requirement for local palliative radiotherapy."),
  note("Pain progression must be supported by clinical and/or radiological evidence of disease progression to count as a PFS event component (Section 4.2.1). An isolated pain score increase without disease evidence is recorded in ADRS but does not trigger the PFS event."),
  new Paragraph({ children: [new PageBreak()] }),
];

// ─── SECTION 5 ────────────────────────────────────────────────────────────────
const section5 = () => [
  h1("5  SAFETY ANALYSIS"),
  blank(),
  h2("5.1  Analysis Population"),
  p("All safety analyses use the Safety (All-Treated) population. Treatment group assignment is based on treatment actually received (ADSL.TRT01A)."),
  blank(),
  h2("5.2  Treatment-Emergent Adverse Events"),
  h3("5.2.1  TEAE Definition"),
  p("An AE is treatment-emergent if it first occurs or worsens in severity on or after the date of the first dose of study drug (ADSL.TRTSDT) through 30 days after the last dose (ADSL.TRTEDTM + 30 days)."),
  p("ADaM variable: ADAE.TRTEMFL = 'Y'. Primary source: SUPPAE.AETRTEM; independently validated against ASTDT >= TRTSDT derivation.", { italic: true }),
  blank(),
  h3("5.2.2  Incidence Tables"),
  p("TEAE incidence is summarized at the MedDRA System Organ Class (SOC) and Preferred Term (PT) levels. The denominator for each PT is the number of subjects with at least one occurrence of that PT (AEOCCFL='Y'). Report:"),
  bullet("All TEAEs: n (%) of patients with \u22651 occurrence per SOC/PT (Table T-14-1)"),
  bullet("Grade \u22653 TEAEs (Table T-14-2)"),
  bullet("Serious TEAEs (AESER='Y') (Table T-14-3)"),
  bullet("TEAEs leading to dose reduction or discontinuation (Table T-14-4)"),
  bullet("Fatal TEAEs within 30 days of last dose (Table T-14-5)"),
  blank(),
  h3("5.2.3  OCCDS v1.1 Episode Merging"),
  p("To avoid inflation of neutropenia incidence counts from recurring episodes within a single myelosuppression cycle, contiguous adverse event episodes are merged per OCCDS v1.1:"),
  bullet("Events with the same CQ02NAM (Customized Query grouping) for a subject are evaluated sequentially by start date."),
  bullet("If a new event starts within 3 days of the prior episode's end date, it is merged into the same continuous episode (CIAESEQ unchanged, AEOCCFL='N')."),
  bullet("If the gap exceeds 3 days, a new episode sequence is assigned (CIAESEQ increments, AEOCCFL='Y' for first record of new sequence)."),
  bullet("Clinical rationale: Cabazitaxel ANC nadir typically occurs Days 8-12; recovery by Days 18-21 of the 21-day cycle. Short-gap re-occurrences represent physiological continuation of the same myelosuppressive episode."),
  note("AEOCCFL='Y' must mark the first record of EACH CIAESEQ, not only the first record in the entire CQ02NAM group. This distinction is critical for accurate incidence denominator counts."),
  blank(),
  h2("5.3  Hematologic Laboratory Safety"),
  p("Hematologic toxicities assessed from LB domain. LBTOXGR in source = CTCAE v3.0 grades (Sanofi-assigned). Map directly to ATOXGR in ADLB."),
  blank(),
  p("Priority parameters for hematology summaries:"),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [1440, 1440, 1440, 1440, 1440, 2160],
    rows: [
      new TableRow({ children: [hdrCell("LBTESTCD",1440),hdrCell("Parameter",1440),hdrCell("G1",1440),hdrCell("G2",1440),hdrCell("G3",1440),hdrCell("G4",2160)] }),
      ...[
        ["ANC","Abs. Neutrophil Count","<LLN–1.5\u00D710\u00B3","\u22651.0–<1.5\u00D710\u00B3","\u22650.5–<1.0\u00D710\u00B3","<0.5\u00D710\u00B3/\u03BCL"],
        ["HGB","Hemoglobin","<LLN–10 g/dL","\u22658–<10 g/dL","\u22656.5–<8 g/dL","<6.5 g/dL"],
        ["PLT","Platelets","<LLN–75\u00D710\u00B3","\u226550–<75\u00D710\u00B3","\u226525–<50\u00D710\u00B3","<25\u00D710\u00B3/\u03BCL"],
        ["WBC","White Blood Cells","<LLN–3.0\u00D710\u00B3","\u22652.0–<3.0\u00D710\u00B3","\u22651.0–<2.0\u00D710\u00B3","<1.0\u00D710\u00B3/\u03BCL"],
      ].map(([tc,tn,g1,g2,g3,g4],i) => new TableRow({
        children: [dataCell(tc,1440,i%2===0,true),dataCell(tn,1440,i%2===0),dataCell(g1,1440,i%2===0),dataCell(g2,1440,i%2===0),dataCell(g3,1440,i%2===0),dataCell(g4,2160,i%2===0)],
      })),
    ],
  }),
  blank(),
  h2("5.4  Concomitant Medications — G-CSF Analysis"),
  p("G-CSF use is a critical confounder for ANC kinetic analyses. The protocol permitted prophylactic G-CSF from Cycle 2 onwards (NOT Cycle 1) at investigator discretion, and after the first episode of Grade \u22653 febrile neutropenia (mandatory)."),
  p("ADCM flags required:"),
  bullet("GCSFFL: G-CSF received Y/N (CMDECOD IN filgrastim, pegfilgrastim, lenograstim)"),
  bullet("GCSFPRFL: Prophylactic G-CSF (CMINDC='PROPHYLAXIS' within 3 days of infusion date)"),
  p("All ANC nadir analyses and Optimus exposure-response models are stratified by GCSFFL. Unstratified analyses without G-CSF adjustment must not be presented as the primary result."),
  new Paragraph({ children: [new PageBreak()] }),
];

// ─── SECTION 6 ────────────────────────────────────────────────────────────────
const section6 = () => [
  h1("6  SUBGROUP ANALYSES"),
  blank(),
  h2("6.1  Pre-specified Subgroups"),
  p("Subgroup analyses are descriptive only. No multiplicity adjustment is applied. Results are presented as forest plots of HR (CbzP vs MP) with 95% CI per subgroup for OS (F-12-1) and PFS (F-12-2). Subgroups with < 10 subjects per arm are flagged but not excluded."),
  blank(),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2520, 3240, 3600],
    rows: [
      new TableRow({ children: [hdrCell("Subgroup Factor",2520),hdrCell("Categories",3240),hdrCell("ADSL Variable",3600)] }),
      ...[
        ["Age","<65 years / \u226565 years","AGEGR1"],
        ["ECOG PS (randomization stratification)","0-1 / 2","ECOGBL"],
        ["Measurable disease (randomization stratification)","Measurable / Non-measurable","MEASDISFL"],
        ["Visceral metastasis","Yes / No","VISCFL"],
        ["Baseline pain","Painful (PPI\u22652 or AS\u226510) / Not painful","PAINBL"],
        ["Baseline ALP","Within normal range / Above ULN","ALPGR1 (derived)"],
        ["Baseline albumin","Within normal range / Below LLN","ALBGR1 (derived)"],
        ["Baseline PSA","Continuous (Cox covariate); categorical TBD by SAP","PSABL"],
        ["Prior docetaxel progression timing","During therapy / After last dose","DOCPROG"],
        ["Prior docetaxel response","Responder / Non-responder","DOCRESP"],
      ].map(([s,c,v],i) => new TableRow({
        children: [dataCell(s,2520,i%2===0,true),dataCell(c,3240,i%2===0),dataCell(v,3600,i%2===0)],
      })),
    ],
  }),
  blank(),
  h2("6.2  Forest Plot Specifications"),
  p("Forest plot panels: OS (primary) and PFS. For each subgroup and arm, report: n events/N at risk; median (95% CI); unstratified HR (95% CI). I-squared statistic for heterogeneity across subgroups. SAS: custom PROC SGPLOT forest macro. R: forestplot package or custom ggplot2."),
  new Paragraph({ children: [new PageBreak()] }),
];

// ─── SECTION 7 ────────────────────────────────────────────────────────────────
const section7 = () => [
  h1("7  EXPLORATORY ANALYSES — PROJECT OPTIMUS"),
  blank(),
  h2("7.1  Context and Regulatory Basis"),
  p("FDA Project Optimus (final guidance August 2024) requires sponsors to optimize oncology dosing based on dose-response and benefit-risk evidence rather than maximum tolerated dose alone. The PROSELICA trial (NCT01308580) subsequently demonstrated non-inferiority of cabazitaxel 20 mg/m\u00B2 vs 25 mg/m\u00B2 for OS with lower toxicity, validating a dose-optimization hypothesis for this compound."),
  p("This re-analysis uses TROPIC PDS data to retrospectively characterize the dose-ANC nadir relationship, providing independent patient-level evidence supporting the PROSELICA dose-reduction decision."),
  blank(),
  h2("7.2  Required ADaM Datasets"),
  bullet("ADEX (PARAMCD: DOSE, PLDOSE, CUMDOSE, RDI, RDIDL, NCYCLE, NDELDOSE, NREDDOSE, ADJAE)"),
  bullet("ADLB (PARAMCD: ANCNADIR, ANCRECDY) — second-pass derivations after primary ADLB"),
  bullet("ADCM (GCSFFL, GCSFPRFL) — G-CSF stratification variable"),
  bullet("ADSL (baseline covariates for regression models)"),
  bullet("ADTTE (PARAMCD: OS, TTOS) — benefit-risk outcome variables"),
  bullet("ADAE — Grade \u22653 and febrile neutropenia incidence"),
  blank(),
  h2("7.3  Analysis Plan"),
  h3("7.3.1  Exposure Characterization (Table T-17-1)"),
  p("Summarize RDI distribution by arm and cycle: n, mean (SD), median (Q1-Q3), % in each RDIDL category (<65% / 65-<85% / \u226585%). Identify proportion requiring dose delays (NDELDOSE>0) and dose reductions (NREDDOSE>0). Source: ADEX."),
  blank(),
  h3("7.3.2  ANC Nadir Analysis Stratified by G-CSF (Table T-17-2)"),
  p("Per cycle and overall, present mean, SD, median, Grade \u22653 %, Grade 4 % for ANC nadir, separately for: G-CSF users (GCSFFL='Y'), G-CSF non-users (GCSFFL='N'), and combined. This is the foundation for all Optimus kinetic claims."),
  blank(),
  h3("7.3.3  ANC Recovery Latency Analysis (Table T-17-3)"),
  p("Days from ANC nadir to ANC recovery (\u22651500/mm\u00B3 = Grade <1) per cycle. Summarized as mean (SD), median (range). Cross-tabulate against dose delay status (NDELDOSE>0 vs 0). This informs the minimum cycle spacing question in dose optimization."),
  blank(),
  h3("7.3.4  Exposure-Response Scatter (Figure F-17-1)"),
  p("Scatter plot of individual RDI (%) on X-axis vs ANC nadir value on Y-axis. One data point per patient per cycle. Stratified by G-CSF (symbol/color). Overlay LOWESS smoothing curve per G-CSF stratum."),
  p("Linear regression: ANC_nadir ~ RDI + GCSFFL + AGE + ALBBL + cycle_number. Report \u03B2 coefficients + 95% CI. SAS: PROC REG + PROC SGPLOT. R: lm() + ggplot2::geom_smooth(method='loess')."),
  blank(),
  h3("7.3.5  Benefit-Risk Table by RDI Tertile (Table T-17-4)"),
  p("Categorize subjects by RDI tertile (T1: <65%, T2: 65-<85%, T3: \u226585%). For each tertile: median OS + 95% CI (KM), % Grade \u22653 any AE (ADAE), % Grade \u22653 neutropenia (ADAE), % febrile neutropenia (ADAE). Report across cabazitaxel arm only (MP arm excluded — different mechanism). This is the core benefit-risk visualization required by Project Optimus methodology."),
  new Paragraph({ children: [new PageBreak()] }),
];

// ─── SECTION 8 ────────────────────────────────────────────────────────────────
const section8 = () => [
  h1("8  ADaM DATASETS AND DATA DERIVATION RULES"),
  blank(),
  h2("8.1  Dataset Overview"),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [1080, 1440, 1920, 4920],
    rows: [
      new TableRow({ children: [hdrCell("Dataset",1080),hdrCell("Structure",1440),hdrCell("Standard",1920),hdrCell("Purpose",4920)] }),
      ...[
        ["ADSL","USUBJID","ADaMIG v1.3","Subject-level covariates, population flags, survival dates, baseline characteristics"],
        ["ADEX","USUBJID PARAMCD","BDS","Per-cycle and summary exposure: RDI, cumulative dose, dose modifications"],
        ["ADCM","USUBJID CMSEQ","OCCDS v1.1","Concomitant medications: G-CSF flags, NACTDT for PFS censoring"],
        ["ADAE","USUBJID AESEQ","OCCDS v1.1","Treatment-emergent AEs with episode merging (CIAESEQ)"],
        ["ADLB","USUBJID PARAMCD AVISITN","BDS","Laboratory safety with analysis windowing and Optimus kinetic params"],
        ["ADRS","USUBJID PARAMCD AVISITN","BDS","Tumor response per RECIST, PSA progression, pain response, PCWG2 bone"],
        ["ADTTE","USUBJID PARAMCD","BDS-TTE","Time-to-event: OS, PFS, TTPSA, TTPAIN, TTOS"],
      ].map(([d,s,std,pur],i) => new TableRow({
        children: [dataCell(d,1080,i%2===0,true),dataCell(s,1440,i%2===0),dataCell(std,1920,i%2===0),dataCell(pur,4920,i%2===0)],
      })),
    ],
  }),
  blank(),
  h2("8.2  Key Derivation Rules"),
  h3("8.2.1  Treatment Start and End Dates"),
  bullet("TRTSDT = min(EXSTDTC) per USUBJID, converted to SAS date. Primary anchor for all ADY calculations."),
  bullet("TRTEDTM = max(EXENDTC) per USUBJID."),
  bullet("ADY = observation date - TRTSDT + 1. Day of first dose = ADY 1. Pre-treatment observations = negative ADY."),
  blank(),
  h3("8.2.2  AE Week-to-Date Conversion (CRITICAL)"),
  p("Source SDTM stores AE timing as AESTWK/AEENWK (integer week numbers). Convert to ISO 8601 dates:"),
  bullet("AESTDTC = RFSTDTC + (AESTWK - 1) \u00D7 7 days (e.g., Week 1 = Day 1-7, Week 2 = Day 8-14)"),
  bullet("AEENDTC = RFSTDTC + (AEENWK - 1) \u00D7 7 + 6 days (last day of the AE week)"),
  bullet("RFSTDTC = DM.RFSTDTC for each subject (first study drug dose date)"),
  p("Document this algorithm in full in the SDRG.", { italic: true }),
  blank(),
  h3("8.2.3  ADLB Analysis Windows"),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [1080, 2400, 1800, 1800, 2280],
    rows: [
      new TableRow({ children: [hdrCell("AVISITN",1080),hdrCell("AVISIT",2400),hdrCell("ADY Low",1800),hdrCell("ADY High",1800),hdrCell("Target Day",2280)] }),
      ...[
        ["0","Baseline","\u2264 0","\u2264 0","Last pre-treatment value"],
        ["1","Cycle 1 Day 8","4","13","8 (nadir window)"],
        ["2","Cycle 1 Day 15","14","17","15 (early recovery)"],
        ["3","Cycle 2 Day 1 Pre","18","24","22 (pre-cycle gate)"],
        ["4","Cycle 2 Day 8","25","34","29 (second nadir)"],
        ["5","Cycle 3 Day 1 Pre","39","45","43 (third cycle gate)"],
        ["99","Unscheduled","All unmatched","—","—"],
      ].map(([n,v,lo,hi,td],i) => new TableRow({
        children: [dataCell(n,1080,i%2===0,true),dataCell(v,2400,i%2===0),dataCell(lo,1800,i%2===0),dataCell(hi,1800,i%2===0),dataCell(td,2280,i%2===0)],
      })),
    ],
  }),
  p("ANL01FL = 'Y' for the single best record per USUBJID \u00D7 PARAMCD \u00D7 AVISITN. Resolution priority: (1) minimum AWDIST (closest to protocol target day); (2) descending ATOXGR. Implementation: no RETAIN statement for ANL01FL; initialize explicitly at each if first.avisitn block."),
  blank(),
  h2("8.3  Validation Against Published Results"),
  p("Pipeline acceptance criterion: independent replication of published Lancet 2010 primary results."),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [3360, 2400, 1680, 1920],
    rows: [
      new TableRow({ children: [hdrCell("Statistic",3360),hdrCell("Published Value",2400),hdrCell("Tolerance",1680),hdrCell("ADaM Source",1920)] }),
      ...[
        ["Median OS — CbzP","15.1 months (95% CI 14.1\u201316.3)","\u00B10.3 months","ADTTE OS"],
        ["Median OS — MP","12.7 months (95% CI 11.6\u201313.7)","\u00B10.3 months","ADTTE OS"],
        ["OS Hazard Ratio","0.70 (95% CI 0.59\u20130.83)","\u00B10.02","ADTTE OS"],
        ["OS Log-rank p-value","< 0.0001","p < 0.001 acceptable","ADTTE OS"],
        ["Grade \u22653 neutropenia — CbzP","82%","\u00B13%","ADAE + ADLB"],
        ["Febrile neutropenia — CbzP","8%","\u00B12%","ADAE"],
        ["PSA response rate — CbzP","39.2%","\u00B12%","ADLB PSAD50"],
        ["PSA response rate — MP","17.8%","\u00B12%","ADLB PSAD50"],
      ].map(([s,pv,tol,src],i) => new TableRow({
        children: [dataCell(s,3360,i%2===0,true),dataCell(pv,2400,i%2===0),dataCell(tol,1680,i%2===0),dataCell(src,1920,i%2===0)],
      })),
    ],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ─── SECTION 9 ────────────────────────────────────────────────────────────────
const section9 = () => [
  h1("9  TFL OUTPUT CATALOGUE"),
  blank(),
  h2("9.1  Table of Outputs"),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [840, 4320, 2160, 2040],
    rows: [
      new TableRow({ children: [hdrCell("ID",840),hdrCell("Title",4320),hdrCell("Datasets",2160),hdrCell("Population",2040)] }),
      ...[
        ["T-11-1","Overall Survival Summary — Median, HR, Events/N","ADTTE","ITT"],
        ["T-11-2","Progression-Free Survival Summary","ADTTE","ITT"],
        ["T-11-3","PSA Response Rate (\u226550% decline confirmed)","ADLB+ADSL","ITT PSA\u226520"],
        ["T-11-4","Objective Response Rate — Measurable Disease","ADRS+ADSL","ITT Measurable"],
        ["T-12-1","OS Sensitivity: RMST at \u03C4=12 months","ADTTE","ITT"],
        ["T-12-2","OS Sensitivity: Landmark at 6 and 12 months","ADTTE","ITT"],
        ["T-13-1","Exposure Summary: Duration, Cycles, Cumulative Dose","ADEX","Safety"],
        ["T-13-2","Dose Modifications: Reductions, Delays, Discontinuations","ADEX","Safety"],
        ["T-13-3","Relative Dose Intensity Summary","ADEX","Safety"],
        ["T-14-1","All TEAEs by SOC and Preferred Term","ADAE","Safety"],
        ["T-14-2","Grade \u22653 TEAEs by SOC and Preferred Term","ADAE","Safety"],
        ["T-14-3","Serious TEAEs (AESER=Y)","ADAE","Safety"],
        ["T-14-4","TEAEs Leading to Dose Reduction or Discontinuation","ADAE","Safety"],
        ["T-14-5","Deaths Within 30 Days of Last Dose","ADAE+ADSL","Safety"],
        ["T-15-1","G-CSF Use by Arm and Cycle","ADCM","Safety"],
        ["T-16-1","Hematology Values Over Time by Arm","ADLB","Safety"],
        ["T-16-2","Worst CTCAE Grade for ANC, HGB, PLT, WBC","ADLB","Safety"],
        ["T-17-1","RDI Distribution by Arm and Cycle","ADEX","Safety"],
        ["T-17-2","ANC Nadir by Cycle Stratified by G-CSF Use","ADLB+ADCM","Safety"],
        ["T-17-3","ANC Recovery Latency vs Dose Delay Status","ADLB+ADEX","Safety"],
        ["T-17-4","Benefit-Risk by RDI Tertile: OS vs Grade\u22653 Tox","ADEX+ADTTE+ADAE","CbzP Safety"],
        ["F-11-1","KM Curve — OS by Arm (Primary)","ADTTE","ITT"],
        ["F-11-2","KM Curve — PFS by Arm","ADTTE","ITT"],
        ["F-12-1","Forest Plot — OS Pre-specified Subgroups","ADTTE+ADSL","ITT"],
        ["F-12-2","Forest Plot — PFS Pre-specified Subgroups","ADTTE+ADSL","ITT"],
        ["F-17-1","Scatter Plot — RDI vs ANC Nadir (Optimus)","ADEX+ADLB+ADCM","Safety CbzP"],
      ].map(([id,title,ds,pop],i) => new TableRow({
        children: [dataCell(id,840,i%2===0,true),dataCell(title,4320,i%2===0),dataCell(ds,2160,i%2===0),dataCell(pop,2040,i%2===0)],
      })),
    ],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ─── SECTION 10 ───────────────────────────────────────────────────────────────
const section10 = () => [
  h1("10  REGULATORY STANDARDS AND COMPLIANCE"),
  blank(),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2880, 2160, 4320],
    rows: [
      new TableRow({ children: [hdrCell("Standard",2880),hdrCell("Version",2160),hdrCell("Application",4320)] }),
      ...[
        ["ADaMIG","v1.3 (FDA mandate 2024-03-15)","All ADaM dataset structures and variable derivations"],
        ["SDTM-IG","3.1.1 (source data as submitted)","Input SDTM interpretation; deviations documented in SDRG"],
        ["OCCDS","v1.1","ADAE episode merging, AEOCCFL denominator logic"],
        ["Define-XML","v2.1 (FDA mandate 2024-04-01)","Dataset metadata, value-level metadata, codelists"],
        ["Submission format","XPT v5 (currently required by FDA)","All ADaM dataset exports"],
        ["NCI CTCAE","v3.0 (as used in TROPIC)","Toxicity grading — reflects trial-era standard"],
        ["RECIST","v1.0 (as used in TROPIC; published 2000)","Tumor response — reflects trial-era standard"],
        ["ICH E9","Statistical Principles for Clinical Trials","Hierarchical multiplicity control framework"],
        ["21 CFR Part 11","Electronic Records","Git version control for audit trail; logrx for R logs"],
        ["ALCOA+","ICH E6(R3)","Attributable, Legible, Contemporaneous, Original, Accurate"],
        ["FDA Project Optimus","August 2024 final guidance","Exploratory dose-response analyses (Section 7)"],
        ["Pinnacle 21","Community CLI (current)","ADaM validation before XPT presentation"],
      ].map(([s,v,a],i) => new TableRow({
        children: [dataCell(s,2880,i%2===0,true),dataCell(v,2160,i%2===0),dataCell(a,4320,i%2===0)],
      })),
    ],
  }),
  blank(),
  h2("10.1  Methodological Caveats (Required in ADRG)"),
  num("CTCAE version: TROPIC used CTCAE v3.0. This SAP applies v3.0 thresholds as in source data. Mapping to v5.0 would change some grade boundaries and is not performed in this analysis."),
  num("RECIST version: TROPIC used RECIST 1.0 (2000). This SAP applies RECIST 1.0. RECIST 1.1 (2009) had not been published at the time of trial design."),
  num("PCWG criteria: Prostate Cancer Working Group 2 (PCWG2) criteria were contemporaneous with TROPIC (2010). Any reference to PCWG3 in exploratory analyses is a retrospective overlay and must be described as such."),
  num("AE week-to-date conversion: AE timing reconstructed from AESTWK/AEENWK week numbers. This introduces a \u00B13-day uncertainty relative to exact calendar dates. Document conversion algorithm in SDRG."),
  num("Data source limitation: PDS data may represent the comparator arm (mitoxantrone) primarily. Verify cabazitaxel arm completeness on the PDS platform before analysis."),
  num("Project Optimus secondary analysis: TROPIC was not prospectively designed for dose optimization. Exploratory findings are hypothesis-generating and consistent with the PROSELICA dose-reduction rationale, not confirmatory."),
  blank(),
  h2("10.2  Data Handling Conventions"),
  bullet("No imputation of missing data except as explicitly specified (e.g., ANCRECDY: if ANC never recovers within cycle, censor at last ANC measurement date)."),
  bullet("Patients non-evaluable for a specific secondary endpoint (e.g., no measurable disease for ORR) are excluded from that endpoint's denominator but included in ITT population tables with appropriate notation."),
  bullet("PSA response evaluated only in patients with baseline PSA \u226520 ng/mL. PSA progression evaluated in ALL ITT patients."),
  bullet("Dates: all dates converted to SAS date format from ISO 8601 using INPUT(var, e8601da.) function. Partial dates imputed as last day of month or first day of month per standard clinical conventions; document specific rules in ADRG."),
  new Paragraph({ children: [new PageBreak()] }),
];

// ─── SECTION 11 ───────────────────────────────────────────────────────────────
const section11 = () => [
  h1("11  VERSION HISTORY AND SIGNATURES"),
  blank(),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [1080, 1800, 3600, 2880],
    rows: [
      new TableRow({ children: [hdrCell("Version",1080),hdrCell("Date",1800),hdrCell("Description",3600),hdrCell("Author",2880)] }),
      new TableRow({ children: [
        dataCell("1.0",1080,false,true), dataCell("2024-01-15",1800), dataCell("Initial SAP — secondary analysis framework. Protocol-derived. Validation target: Lancet 2010 published results.",3600), dataCell("[Programmer Name]",2880),
      ]}),
    ],
  }),
  blank(),
  blank(),
  h2("Signature Block"),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [3120, 3120, 3120],
    rows: [
      new TableRow({ children: [hdrCell("Role",3120), hdrCell("Name",3120), hdrCell("Date",3120)] }),
      ...[
        ["Lead Statistical Programmer","[Name]",""],
        ["Independent Reviewer","[Name]",""],
        ["Clinical Domain Reviewer","[Name]",""],
      ].map(([r,n,d],i) => new TableRow({
        children: [
          dataCell(r,3120,i%2===0,true),
          new TableCell({ borders: allBorders, width:{size:3120,type:WidthType.DXA}, shading:{fill:i%2===0?LGRAY:WHITE,type:ShadingType.CLEAR}, margins:{top:200,bottom:200,left:120,right:120}, children:[new Paragraph({children:[new TextRun("")]})] }),
          new TableCell({ borders: allBorders, width:{size:3120,type:WidthType.DXA}, shading:{fill:i%2===0?LGRAY:WHITE,type:ShadingType.CLEAR}, margins:{top:200,bottom:200,left:120,right:120}, children:[new Paragraph({children:[new TextRun("")]})] }),
        ],
      })),
    ],
  }),
  blank(),
  blank(),
  h2("Appendix A: Abbreviations"),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [1440, 7920],
    rows: [
      new TableRow({ children: [hdrCell("Abbreviation",1440), hdrCell("Definition",7920)] }),
      ...[
        ["ADaM","Analysis Data Model"],
        ["ADSL/ADEX/ADCM/ADAE/ADLB/ADRS/ADTTE","ADaM dataset names per this SAP"],
        ["ADaMIG","ADaM Implementation Guide"],
        ["AE","Adverse Event"],
        ["ALP","Alkaline Phosphatase"],
        ["ANC","Absolute Neutrophil Count"],
        ["AS","Analgesic Score (morphine equivalents)"],
        ["BSA","Body Surface Area"],
        ["CbzP","Cabazitaxel + Prednisone"],
        ["CNSR","Censoring variable (0=event, 1=censored) in ADTTE"],
        ["CR","Complete Response"],
        ["CTCAE","Common Terminology Criteria for Adverse Events"],
        ["ECOG PS","Eastern Cooperative Oncology Group Performance Status"],
        ["G-CSF","Granulocyte Colony-Stimulating Factor"],
        ["HR","Hazard Ratio"],
        ["ICH","International Council for Harmonisation"],
        ["ITT","Intent-to-Treat Population"],
        ["KM","Kaplan-Meier"],
        ["LLN","Lower Limit of Normal"],
        ["mCRPC","Metastatic Castration-Resistant Prostate Cancer"],
        ["MedDRA","Medical Dictionary for Regulatory Activities"],
        ["MP","Mitoxantrone + Prednisone"],
        ["NCI","National Cancer Institute"],
        ["NACTDT","Date of New Anti-Cancer Therapy"],
        ["ORR","Objective Response Rate"],
        ["OS","Overall Survival"],
        ["OCCDS","Oncology Customized Query Data Standard"],
        ["PD","Progressive Disease"],
        ["PDS","Project Data Sphere"],
        ["PFS","Progression-Free Survival"],
        ["PPI","Present Pain Intensity (McGill-Melzack scale)"],
        ["PR","Partial Response"],
        ["PSA","Prostate-Specific Antigen"],
        ["RECIST","Response Evaluation Criteria in Solid Tumors"],
        ["RDI","Relative Dose Intensity"],
        ["RMST","Restricted Mean Survival Time"],
        ["SAP","Statistical Analysis Plan"],
        ["SDTM","Study Data Tabulation Model"],
        ["TEAE","Treatment-Emergent Adverse Event"],
        ["TFL","Tables, Figures, Listings"],
        ["ULN","Upper Limit of Normal"],
      ].map(([a,d],i) => new TableRow({
        children: [dataCell(a,1440,i%2===0,true), dataCell(d,7920,i%2===0)],
      })),
    ],
  }),
];

// ─── ASSEMBLE DOCUMENT ────────────────────────────────────────────────────────
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: WHITE },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: NAVY },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial", color: BLUE },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [
        { level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 540, hanging: 360 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "\u25E6", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 900, hanging: 360 } } } },
      ]},
      { reference: "numbers", levels: [
        { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 540, hanging: 360 } } } },
      ]},
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BLUE } },
          children: [
            new TextRun({ text: "TROPIC Trial (EFC6193) — Statistical Analysis Plan v1.0", font: "Arial", size: 18, color: "666666" }),
            new TextRun({ text: "   |   CONFIDENTIAL — Secondary Analysis / Portfolio Project", font: "Arial", size: 18, color: "999999" }),
          ],
          spacing: { after: 120 },
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: BLUE } },
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
          children: [
            new TextRun({ text: "Data Source: Project Data Sphere — Sanofi US | ADaMIG v1.3", font: "Arial", size: 16, color: "888888" }),
            new TextRun({ text: "\tPage ", font: "Arial", size: 16, color: "888888" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "888888" }),
          ],
          spacing: { before: 120 },
        })],
      }),
    },
    children: [
      ...titlePage(),
      ...section1(),
      ...section2(),
      ...section3(),
      ...section4(),
      ...section5(),
      ...section6(),
      ...section7(),
      ...section8(),
      ...section9(),
      ...section10(),
      ...section11(),
    ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('./TROPIC_SAP_v1.0.docx', buffer);
  console.log('Done');
});
