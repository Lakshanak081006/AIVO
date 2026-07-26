# Non-Functional Requirements

- **Usability:** responsive interface, clear errors and progress.
- **Reliability:** retries, fallback data, transaction rollback and failure isolation.
- **Security:** hashed passwords, JWT protection, environment-based secrets and no real payments.
- **Maintainability:** modular agents, services, schemas, repositories and reusable React components.
- **Performance:** parallel independent search tasks with `asyncio.gather`.
- **Portability:** SQLite for zero-setup local demos and PostgreSQL through Docker Compose.
- **Transparency:** persistent logs, task status, decision reasons and version history.
