export const meta = {
  name: 'docs-rewrite-review',
  description: 'Fix + review every hand-written docs page against the live engine API; stage runnable snippets',
  phases: [
    { title: 'Fix', detail: 'Sonnet: correct code blocks against ground truth, stage runnable snippets' },
    { title: 'Review', detail: 'Opus: verify against the compiled API, catch hallucinated APIs, set disposition' },
    { title: 'Finalize', detail: 'Sonnet: apply review patches, stamp frontmatter' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args) : args
const ENGINE = A.engineRoot
const SITE = A.siteRoot
const CHEAT = A.cheatsheet
const VERSION = A.version
const COMMIT = A.commit

const FIX_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['page', 'code_blocks_total', 'code_blocks_changed', 'defects', 'snippets_staged', 'notes'],
  properties: {
    page: { type: 'string' },
    code_blocks_total: { type: 'integer' },
    code_blocks_changed: { type: 'integer' },
    defects: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['location', 'problem', 'fix'],
        properties: {
          location: { type: 'string' },
          problem: { type: 'string' },
          fix: { type: 'string' },
        },
      },
    },
    snippets_staged: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['file', 'ran', 'detail'],
        properties: {
          file: { type: 'string' },
          ran: { type: 'string', enum: ['pass', 'fail', 'not-run'] },
          detail: { type: 'string' },
        },
      },
    },
    notes: { type: 'string' },
  },
}

const REVIEW_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['page', 'verdict', 'api_errors_remaining', 'prose_issues', 'required_patches', 'final_disposition', 'summary'],
  properties: {
    page: { type: 'string' },
    verdict: { type: 'string', enum: ['approved', 'needs_changes'] },
    api_errors_remaining: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['location', 'problem', 'correct_form'],
        properties: {
          location: { type: 'string' },
          problem: { type: 'string' },
          correct_form: { type: 'string' },
        },
      },
    },
    prose_issues: { type: 'array', items: { type: 'string' } },
    required_patches: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['location', 'change'],
        properties: {
          location: { type: 'string' },
          change: { type: 'string' },
        },
      },
    },
    final_disposition: { type: 'string', enum: ['current', 'needs-review', 'rewrite-pending'] },
    summary: { type: 'string' },
  },
}

const FINALIZE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['page', 'patches_applied', 'frontmatter_stamped', 'final_disposition', 'notes'],
  properties: {
    page: { type: 'string' },
    patches_applied: { type: 'integer' },
    frontmatter_stamped: { type: 'boolean' },
    final_disposition: { type: 'string' },
    notes: { type: 'string' },
  },
}

function fixPrompt(page) {
  return `You are correcting one McRogueFace documentation page so every code sample matches the
engine that ships today. This is mechanical correction work — accuracy over creativity.

PAGE (edit it IN PLACE with Edit): ${SITE}/${page.path}
Its self-declared disposition is "${page.disposition}" — do NOT trust that grade; verify from scratch.

GROUND TRUTH — read this file FIRST and treat it as authority:
  ${CHEAT}
It lists the exact known-broken→correct API mappings and the 58 real exported classes.

Also available to consult (grep/Read as needed):
  - ${ENGINE}/docs/API_REFERENCE_DYNAMIC.md   (authoritative signatures)
  - ${ENGINE}/tests/snippets/*.py             (130 proven-correct examples)

DO:
1. Read the page. Find every fenced code block (\`\`\`python and \`\`\`).
2. For each block, check every mcrfpy usage against ground truth. Fix broken APIs in place
   with Edit. If a block uses \`mcrfpy.Animation\`, \`add_layer("...")\`, \`sceneUI\`/\`setScene\`/
   \`createScene\`/\`keypressScene\`, \`GridPoint.color\`, \`compute_astar_path\`, \`entity.gridstate\`,
   or any \`mcrfpy.X\` where X is not one of the 58 exports — it is WRONG; correct it.
3. Fix prose that describes the old/broken behavior so it matches the corrected code.
4. Do NOT touch the frontmatter — a later step stamps it. Do NOT set disposition.
5. \`tilesprite\` is legacy but NOT broken — leave it, optionally note the TileLayer form.

STAGE RUNNABLE SNIPPETS:
For each code block that is (or can trivially be completed into) a COMPLETE self-contained
program per the cheatsheet's rules (imports mcrfpy, builds a Scene, sets current_scene,
appends a child, no sys.exit, no external files), extract it to:
  ${ENGINE}/tests/snippets/_staging/${page.slug}__NN.py   (NN = 01, 02, ...)
Then VALIDATE it (cwd ${ENGINE}):
  LD_LIBRARY_PATH=build/lib build/mcrogueface --headless --exec tests/snippets/_staging/${page.slug}__NN.py --exec tests/snippets/_harness.py
Passes iff output has SNIPPET_OK and no Traceback. If it FAILS, fix the snippet and rerun
until it passes. If it cannot be made a complete runnable program, delete the staged file
and leave the code inline (corrected) — mark it not-run. Do not invent snippets for pages
that are pure prose/reference (many objects/*.md just document properties).

Return the structured report. Be honest about what you could not verify.`
}

function reviewPrompt(page, fix) {
  return `You are the REVIEW gate for one McRogueFace documentation page that a first-pass agent just
corrected. Your job is to catch what it missed or got wrong — hallucinated APIs, signatures
that don't exist, prose that still contradicts the code, and to set the final disposition.
Be adversarial: assume the fix is incomplete until you've checked it against the compiled API.

PAGE (already edited by the fix pass): ${SITE}/${page.path}

GROUND TRUTH:
  - ${CHEAT}                                   (known-broken→correct, 58 real exports)
  - ${ENGINE}/docs/API_REFERENCE_DYNAMIC.md    (authoritative signatures — grep it to VERIFY
     every method/property name and argument the page now uses actually exists)
  - ${ENGINE}/tests/snippets/*.py              (proven usage)

The fix pass reported:
${JSON.stringify(fix, null, 2)}

DO:
1. Re-read the page's code blocks. For every mcrfpy class, method, property, and keyword
   argument, CONFIRM it exists with that signature in API_REFERENCE_DYNAMIC.md. Anything you
   cannot confirm is an api_error_remaining with the correct_form.
2. Check prose still matches code. Check the staged snippets the fix pass claims PASS are
   genuinely complete programs (you may re-run one if unsure, same command as the fix pass).
3. Decide final_disposition:
     - "current": every code sample verified correct against the compiled API, prose matches.
     - "needs-review": mostly right but a residual concern you can't resolve from the repo.
     - "rewrite-pending": still materially broken.
4. If verdict is needs_changes, list required_patches CONCRETELY (location + exact change) so
   a mechanical follow-up can apply them without judgement. Do not edit the page yourself.

Return the structured verdict.`
}

function finalizePrompt(page, review) {
  return `Finalize one McRogueFace docs page. Mechanical only.

PAGE (edit IN PLACE): ${SITE}/${page.path}

The reviewer returned:
${JSON.stringify(review, null, 2)}

DO:
1. If verdict was needs_changes, apply EACH required_patch exactly as described, using Edit.
   Apply nothing the reviewer did not ask for.
2. Update the YAML frontmatter (between the first two \`---\` lines). Under the top-level
   \`mcrf:\` key set/replace these three keys (keep all other frontmatter untouched):
       disposition: ${review ? review.final_disposition : 'needs-review'}
       verified: "${VERSION}"
       verified_commit: ${COMMIT}
   If a \`verified:\`/\`verified_commit:\` line already exists, replace its value; otherwise add
   it directly under the existing \`disposition:\` line at the same indentation.
Return the structured report (patches_applied = count you applied; frontmatter_stamped true
once the three keys are set).`
}

phase('Fix')
log(`Rewriting ${A.pages.length} docs pages: fix (Sonnet) -> review (Opus) -> finalize (Sonnet)`)

const results = await pipeline(
  A.pages,
  (page) => agent(fixPrompt(page), {
    label: `fix:${page.path}`, phase: 'Fix', model: 'sonnet', effort: 'medium', schema: FIX_SCHEMA,
  }).then(fix => ({ page, fix })),

  (prev, page) => {
    if (!prev || !prev.fix) return { page, fix: null, review: null }
    return agent(reviewPrompt(page, prev.fix), {
      label: `review:${page.path}`, phase: 'Review', model: 'opus', effort: 'high', schema: REVIEW_SCHEMA,
    }).then(review => ({ page, fix: prev.fix, review }))
  },

  (prev, page) => {
    const review = prev ? prev.review : null
    return agent(finalizePrompt(page, review), {
      label: `finalize:${page.path}`, phase: 'Finalize', model: 'sonnet', effort: 'low', schema: FINALIZE_SCHEMA,
    }).then(fin => ({
      page: page.path,
      disposition_before: page.disposition,
      fix: prev ? prev.fix : null,
      review,
      finalize: fin,
    }))
  },
)

const clean = results.filter(Boolean)
const staged = []
for (const r of clean) {
  for (const s of (r.fix && r.fix.snippets_staged) || []) {
    staged.push({ page: r.page, file: s.file, ran: s.ran, detail: s.detail })
  }
}
const byDisp = {}
for (const r of clean) {
  const d = (r.finalize && r.finalize.final_disposition) || (r.review && r.review.final_disposition) || 'unknown'
  byDisp[d] = (byDisp[d] || 0) + 1
}
const needsChanges = clean.filter(r => r.review && r.review.verdict === 'needs_changes')
    .map(r => ({ page: r.page, disposition: r.review.final_disposition, summary: r.review.summary,
                 api_errors: (r.review.api_errors_remaining || []).length }))
const stillBroken = clean.filter(r => (r.finalize && r.finalize.final_disposition) === 'rewrite-pending'
    || (r.review && r.review.final_disposition === 'rewrite-pending'))
    .map(r => r.page)

log(`Done. dispositions: ${JSON.stringify(byDisp)}; staged snippets: ${staged.length}`)

return {
  pages_processed: clean.length,
  pages_expected: A.pages.length,
  disposition_counts: byDisp,
  staged_snippets: staged,
  pages_needing_changes: needsChanges,
  still_rewrite_pending: stillBroken,
}
