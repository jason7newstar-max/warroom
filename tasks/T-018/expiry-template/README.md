# 7-Day Free Preview Expiry Template

Reusable client-side pattern for ONE TEN free-tier preview sites.

## How it works

Each free preview includes:

- `window.ONE_TEN_PREVIEW.deployedAt`
- `window.ONE_TEN_PREVIEW.expiresAfterDays`
- `expiry.js`
- an `#expired-template` HTML template

When the browser loads the page, `expiry.js` checks:

```js
Date.now() > new Date(deployedAt).getTime() + expiresAfterDays * 24 * 60 * 60 * 1000
```

If expired, the page is replaced with:

> This preview expired. Upgrade to keep it live for $9.99/mo.

## Use in a new free site

1. Copy `base/expiry.js` into the client site.
2. Add the `#expired-template` block from `base/index.html`.
3. Set `deployedAt` to the deploy timestamp.
4. Keep `expiresAfterDays: 7` unless the offer changes.

Example:

```html
<script>
  window.ONE_TEN_PREVIEW = {
    deployedAt: "2026-06-06T00:00:00-04:00",
    expiresAfterDays: 7
  };
</script>
<script src="expiry.js"></script>
```

## Demo

`demo-expired/` sets `deployedAt` to `2026-05-29T00:00:00-04:00`, eight days before June 6, 2026, so it renders the expired upsell screen immediately.

Run locally from this repo:

```sh
python3 -m http.server 4180 --directory tasks/T-018/expiry-template/demo-expired
```

Then open `http://localhost:4180`.
