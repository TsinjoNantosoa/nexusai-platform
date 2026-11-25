<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.

## What Lovable manages

Rules outside this block are the project's own. Change the pieces below in
Lovable, not by hand. With the [Lovable MCP](https://mcp.lovable.dev)
connected, `send_message` asks Lovable to do it; otherwise ask the user to
use the editor.

- **Database.** Do not add or edit `supabase/migrations/` or `drizzle/`.
  Ask Lovable to change the schema.
- **Generated files.** Do not edit a file whose header says it is automatically
  generated.
- **AI gateway.** Keep model calls on Lovable's gateway, and keep
  `LOVABLE_API_KEY` out of browser code.
- **Connectors.** Lovable provides native connectors. `list_connectors` shows
  which are enabled; `add_connector` only returns the dashboard link. When a
  connector is enabled, calls go through the connector gateway and need
  `LOVABLE_API_KEY`. When Lovable does not provide one, users can bring their
  own key and store it in Secrets.
- **Secrets.** Lovable manages them. Do not put secret values in the repo.
<!-- LOVABLE:END -->

## Frontend architecture

- Keep the existing TanStack Start bootstrap and file-based TanStack Router; the user approved replacing source React Router navigation so URL patterns remain portable within the supported runtime.
- Separate browser-safe domain types, deterministic in-memory mock services and cookie-based external HTTP transport; UI hooks consume one typed interface so FastAPI integration does not require rewriting financial or conversational screens.
- Store demonstration identities and private content only in browser memory, never module-scoped SSR state or persistent caches; refresh clears the fictional session by design.
- Define all visual roles in global semantic tokens and use the existing shadcn controls; route heads own page metadata and shared chrome surrounds the root Outlet.
- Use one guarded wrapper for generated offline service-worker registration; private APIs and authenticated or payment navigations are never cached.
