# ONE TEN War Room Web

Dependency-free command center for the war-room repo.

```sh
cd web
npm start
```

Open `http://localhost:4173`.

The browser fetches the public GitHub sources directly:

- `https://raw.githubusercontent.com/jason7newstar-max/warroom/main/BOARD.md`
- `https://api.github.com/repos/jason7newstar-max/warroom/commits`

That means `public/` can run as a static Vercel front-end with no local filesystem or local git dependency. The Node server is only for local development and exposes `/api/state` as a GitHub-first/local-fallback endpoint. It does not call any LLM or OpenRouter API.
