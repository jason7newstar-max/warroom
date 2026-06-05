# ONE TEN War Room Web

Dependency-free command center for the war-room repo.

```sh
cd web
npm start
```

Open `http://localhost:4173`.

The server reads `../BOARD.md` and `git log` on every `/api/state` request. It does not call any LLM, OpenRouter, or external API.
