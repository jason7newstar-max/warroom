# T-021 CMS Stack Eval - Mini Recommendation

**Author:** Mini  
**Date:** 2026-06-06  
**Scope:** Best CMS + client handoff stack for ONE TEN static-site + Vercel pipeline: many small client sites, low cost, fast handoff, client can edit copy/images/SEO, ONE TEN keeps master control.

## Recommendation

Use **TinaCMS as the default small-client handoff stack**, with **Sanity as the paid/pro tier**, and do **not** build the custom dashboard + MongoDB path yet.

The winning default is:

**Next.js or static Astro/Next site on Vercel + TinaCMS/TinaCloud + GitHub content files + Vercel deploy hooks.**

Why: Tina is Git-backed, has visual editing, and its free plan currently includes **2 users, 2 roles, 1 project**. That maps directly to our micro-site handoff: ONE TEN admin + one client editor. Content stays as Markdown/JSON/MDX in a repo we own, Vercel remains under us, and the client edits only constrained fields.

Use **Sanity** when the client is paying a real monthly retainer or needs a more polished hosted content studio, heavier media/content modeling, or multiple editors. Sanity Free has 20 seats, but only **Administrator** and **Viewer** roles; real **Editor/Contributor** roles are on Growth at **$15/seat/month**, so it is not the lowest-cost default if we care about keeping client permissions tight.

## Ranking For Our Case

| Rank | Stack | Best use | Cost fit | Handoff/control | Verdict |
|---|---|---|---:|---|---|
| 1 | **TinaCMS** | Micro-brand sites, static content, visual edits | **Best** | Git/Vercel remain ours; client edits content files through UI | **Default** |
| 2 | **Sanity** | Paid/pro sites, more structured content, multi-editor clients | Medium | Clean hosted Studio; proper client Editor role requires Growth | **Upsell tier** |
| 3 | **Decap/Netlify CMS** | Ultra-cheap simple static sites where UX is less important | Best | Git-backed, but auth/editor UX is rougher | Backup only |
| 4 | **Payload** | Real app backend, auth, e-commerce-ish workflows, complex admin | Poor for tiny sites | We own infra, but must operate DB/storage/app runtime | Defer |
| 5 | **Custom dashboard + MongoDB** | Proprietary SaaS product with repeated app logic | Worst now | Full control, full maintenance burden | Do not build yet |

## Option Notes

### TinaCMS - Default

**Fit:** strongest match for many small static sites.

Pros:
- Git-backed content: copy, images metadata, SEO fields live in the client repo as Markdown/JSON/MDX.
- Visual editing is easier to hand off than a generic form CMS.
- Free tier is enough for the common handoff: ONE TEN + one client editor.
- Works naturally with our existing GitHub + Vercel pipeline.
- Master control stays clean: we own repo, Vercel, domain, schema, layout, and deploy process.

Cons:
- One Tina project per client site; paid plans are also per project.
- Client edits create Git commits, so repo hygiene and branch/deploy rules matter.
- Not ideal for complex relational content or large editorial teams.

Recommended setup:
- `content/site.json`: global hero, CTAs, footer, SEO.
- `content/sections/*.json`: constrained repeatable sections/cards.
- `public/uploads` or Tina media path for images.
- Tina schema exposes only safe fields: text, image, alt text, SEO title/description, social image.
- Vercel auto-deploys after content commit.

### Sanity - Paid/Pro Tier

**Fit:** best hosted CMS experience, but not the lowest-cost strict-permission default.

Pros:
- Hosted content lake and Studio mean low infrastructure burden.
- Strong schema/content modeling, image pipeline, APIs, and webhooks.
- Better for multiple editors, draft/publish workflows, larger content sets, and retainer clients.

Cons:
- Free plan roles are Administrator/Viewer only; proper Editor/Contributor roles require Growth.
- Content lives in Sanity, not Git, so full export/backup policy is required.
- Per-seat Growth cost matters across many small low-budget clients.

Use when:
- Client pays for CMS handoff as a monthly line item.
- Client needs 2+ editors, scheduled/draft workflow, or content beyond simple site copy.
- We want cleaner non-technical editorial UX than Tina and can price it into the retainer.

### Decap / Netlify CMS - Backup

**Fit:** zero-cost Git CMS for simple static sites, but weaker handoff polish.

Pros:
- Open-source, Git-based, stores content in repo.
- Can run with static sites and does not require Netlify hosting.
- Very low vendor cost.

Cons:
- Auth setup is the recurring pain point, especially outside Netlify Identity/Git Gateway.
- Editor UX feels older than Tina/Sanity.
- YAML config and previews get clunky as sites vary.

Use only for:
- Tiny budget sites where free/open-source beats editing polish.
- Internal experiments or sites where the client is tolerant of a simpler admin UI.

### Payload - Defer

**Fit:** excellent when we are building a real Next.js app backend, not a cheap static-site handoff layer.

Pros:
- Code-first, open-source, self-hostable.
- Strong admin panel, access control, auth, media handling, REST/GraphQL APIs.
- Supports MongoDB, Postgres, and SQLite adapters.

Cons:
- Requires operating an app runtime plus database/storage.
- Payload Cloud new project deployment is currently paused after the Figma acquisition; self-hosting remains the path.
- More engineering and maintenance than micro-brand sites need.

Use later if:
- ONE TEN launches a reusable hosted website platform/SaaS.
- A client needs accounts, gated content, forms/workflows, commerce-like data, or custom operational tools.

### Custom Dashboard + MongoDB - Do Not Build Yet

This is the video-style approach, but it is wrong for our current volume economics.

Pros:
- Full control over UI, permissions, data, billing, and multi-tenant product direction.
- Could become a proprietary ONE TEN platform later.

Cons:
- We would own auth, uploads, image processing, validation, audit logs, backups, security, admin UX, migrations, support, and incident response.
- MongoDB adds per-client or shared-tenant data architecture decisions before we have proven demand.
- Slower handoff than adopting Tina/Sanity now.

Decision: revisit only after 10+ paid CMS clients reveal repeated needs that Tina/Sanity cannot solve.

## Recommended Client-Handoff Model

For every CMS site:

- ONE TEN owns GitHub repo, Vercel project, environment variables, domain/DNS, CMS project, and schema.
- Client gets editor access only.
- Client can edit copy, approved images, alt text, SEO title, SEO description, Open Graph image, product/service cards, hours/contact/social links.
- Client cannot edit layout, code, pricing logic, scripts, analytics, deployment settings, or domains.
- Handoff includes a 15-minute screen recording plus a one-page field guide.
- Monthly retainer covers hosting oversight, content support, backups, minor design/code changes, and emergency rollback.

## Template Build Tasks

1. Build `one-ten-client-site-template` with Next.js or Astro, Vercel, TinaCMS, and a minimal schema.
2. Add content files for: `site`, `seo`, `hero`, `sections`, `gallery`, `faq`, `contact`.
3. Add validation: max lengths, required alt text, image aspect notes, SEO preview fields.
4. Add Vercel deploy hook / GitHub workflow notes for client edits.
5. Add rollback playbook: revert bad client content commit, redeploy.
6. Add pricing package:
   - Basic CMS handoff: Tina, 1 editor, included in setup.
   - Pro CMS handoff: Sanity Growth, client pays CMS/editor cost plus ONE TEN retainer.
   - Custom CMS/app: Payload/custom only as scoped project.

## Final Decision

**Default:** TinaCMS.  
**Upsell:** Sanity.  
**Backup:** Decap.  
**Defer:** Payload.  
**Reject for now:** custom dashboard + MongoDB.

This gives ONE TEN the fastest path to sell self-editable micro-sites without becoming a CMS infrastructure company.

## Sources Checked

- TinaCMS pricing: https://tina.io/pricing
- TinaCMS docs: https://tina.io/docs
- Sanity pricing: https://www.sanity.io/pricing
- Sanity roles docs: https://www.sanity.io/docs/user-guides/roles
- Decap overview: https://decapcms.org/docs/intro/
- Payload overview: https://payloadcms.com/docs/getting-started/what-is-payload
- Payload database docs: https://payloadcms.com/docs/database/overview
- Payload Cloud update: https://payloadcms.com/cloud-pricing
