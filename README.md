# Telegram Structure Cloner

Read-only Telegram source inspection and blueprint export for later channel, group, supergroup, and forum structure replication.

M1 exports a versioned `blueprint.json` from an existing Telegram dialog. It does not copy messages or members, and it never modifies the source.

## What M1 Captures

- Telethon user authentication with a persistent local session.
- Interactive source dialog selection.
- Source identity for channels, groups, supergroups, megagroups, broadcast channels, and forums.
- Full chat/channel settings that Telegram exposes through the user account.
- Default banned rights and admin rights metadata where available.
- Forum topic list and topic metadata where available.
- Configuration media metadata such as chat photo identifiers and document/photo references exposed by Telegram.
- Unsupported, unavailable, or permission-limited properties in `unsupported_properties`.

## What M1 Does Not Do

- Does not copy messages.
- Does not copy members or invite users.
- Does not create or modify destination chats.
- Does not mutate source settings, permissions, topics, usernames, photos, reactions, or linked chats.

## Setup

1. Create a Telegram app at <https://my.telegram.org/apps>.
2. Copy `.env.example` to `.env`.
3. Fill in `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`.
4. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Export A Blueprint

```bash
python -m telegram_structure_cloner export --output blueprint.json
```

You can also pass a source by username, invite link, numeric ID, or dialog name:

```bash
python -m telegram_structure_cloner export --source @source_channel --output blueprints/source.blueprint.json
```

## Blueprint Contract

The export format is versioned:

```json
{
  "schema_version": "1.0.0",
  "exported_at": "2026-09-24T00:00:00Z",
  "source": {},
  "settings": {},
  "permissions": {},
  "forum": {},
  "configuration_media": {},
  "unsupported_properties": []
}
```

Later milestones should add destination planning, creation, replication, and verification without changing M1's read-only source inspection behavior.

## Safety Notes

This project uses only read-oriented Telethon calls in M1. The codebase keeps export logic separate from future replication modules so mutation features can be reviewed independently before they are added.

## Reference

MR-PR0G/Telegram-channel-cloner is useful as a practical Telethon reference for authentication/session flow and Telegram entity handling. This project intentionally starts from a safer, modular read-only architecture before adding destination writes.
