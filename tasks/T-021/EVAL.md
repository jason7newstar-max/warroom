# T-021 EVAL — Adopt plan for the "Claude→client-site + CMS + handoff" workflow

**Author:** Karen · 2026-06-06 · (Mini = deep CMS-stack eval, Gemma = 3rd opinion → both say: adopt the self-edit/handoff layer for scale)

## TL;DR
We already nail **Claude-build + Vercel-deploy**. The Jack Roberts workflow's real upgrade for ONE TEN is **one layer**: the **CMS / client-self-edit / handoff** piece — it's what turns our one-off micro-sites into a *repeatable, retainer-able product* instead of bespoke throwaways. Adopt that, plus a **lightweight design-reference sourcing habit** for UI polish. Skip the rest (MongoDB, Kie.ai) — over-engineering for our <10K micro-brand niche.

---

## (a) CMS / self-edit / HANDOFF — the scaling layer ✅ ADOPT

### What the client actually needs to self-edit
For a micro-brand site it's a *small, fixed* set: hero headline/sub, a few product/section cards, images, hours/contact, SEO title+description. **Not** a general-purpose CMS. The win is a **constrained schema** exposing only those fields — client can't break layout.

### Stack options (vs Vercel + our motion)

| Option | Where content lives | Client UX | Ops per site | Handoff / master-control | Verdict |
|---|---|---|---|---|---|
| **Decap** (git-based) | our git repo | weak; auth = git provider | low | client edits = commits to our repo; bad for non-tech | ❌ skip |
| **TinaCMS** | our git repo + visual | **WYSIWYG on the live page** (great) | low–med | content-in-repo; 1 repo/client | ✅ secondary |
| **Sanity** (hosted headless) | Sanity cloud dataset | clean Studio, role-based | **near-zero** | invite client as *Editor*, we stay *Admin*; we keep code+Vercel+domain | ✅ **primary** |
| **Payload** (Next-native) | our DB (Mongo/PG) | powerful admin | **high** (DB + host/client) | full data ownership | ❌ defer — too much infra for micro-sites |

### RECOMMENDATION → **Sanity-based "ONE TEN Editor" template** (default tier)
- **Why Sanity:** hosted (no DB/infra per client = the opposite of the Mongo path), generous free tier that covers micro-clients, real role-based access for a *clean handoff*, structured content + GROQ, first-class Vercel fit (publish → webhook → ISR/`revalidateTag`). It scales to *many tiny sites* because each is near-zero ops.
- **Build once, reuse:** a Next.js + Sanity starter with a tightly-scoped schema (hero, cards, images, SEO only). New client = clone template + new Sanity project/dataset.
- **Handoff = master-control model:**
  - We own: GitHub repo, Vercel project, domain/DNS, Sanity project (Admin/Owner).
  - Client gets: scoped **Sanity Studio Editor invite** — edit copy/images/SEO, nothing else.
  - Billing lever: keep master control = **monthly retainer**; *full* ownership transfer (repo/Vercel/domain/Sanity) = one-time handoff fee.
- **Secondary tier — TinaCMS** when a client specifically wants *visual, on-page* editing and content-in-repo is fine. Keep as an option, not the default.
- **Do NOT** adopt Payload + MongoDB for this niche — it's per-site DB + hosting ops we don't want at volume. Revisit only if a client needs real app/data backend.

---

## (b) Design-reference sourcing (Dribbble + Firecrawl) ✅ ADOPT (lightweight)

- **Dribbble** — manual, high-ROI: per project, curate 2–4 UI reference shots and feed them to Claude as visual targets ("match this layout/energy"). No automation; just make it a standard pre-build step. Biggest single lever on UI polish for near-zero cost.
- **Firecrawl** — API, modest cost: scrape a named reference/competitor site → clean structured markdown (section flow, copy, hierarchy) → use as a **scaffold/brief** before building. Also good for migrating a client's existing-site content. Best fit with our **T-020 spec-makeover** motion ("make me a site like X" → scrape X → brief).
- **Kie.ai (image gen)** — ❌ skip, redundant. We already have higgsfield/Neon/Dali image pipeline.

---

## Concrete adopt decision
1. **BUILD: Next.js + Sanity "ONE TEN Editor" template** — constrained schema, role-scoped client invites, Vercel publish→revalidate webhook, + a 1-page **handoff/master-control playbook**. *Highest-leverage adoption — converts one-off micro-sites into a recurring product.*
2. **ADD: design-reference pre-build step** — Dribbble curated board (manual) + Firecrawl reference→brief (API).
3. **SKIP:** Payload+MongoDB (over-infra), Kie.ai (have it).

**Next step:** stand up the template repo as proof and **pilot it on the T-020 matcha prototype** (give that client a Studio login) to validate the self-edit + handoff loop end-to-end before rolling it out.
