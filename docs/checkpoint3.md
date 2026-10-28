# Checkpoint 3 Implementation Notes

## Project plan scope

Checkpoint 3 adds generated sample horse data, basic matching filters, and left/right swipes. Horse profiles and chats remain checkpoint 4 features; the matching page links to clearly labeled placeholders for those destinations.

## Database changes

`schema.sql` adds two tables:

- `horses` contains stable sample horse IDs, names, breeds, ages, interests, and an optional picture URL. Startup inserts sample records with `INSERT OR IGNORE`, so starting the app again does not reset horse data.
- `swipes` contains a user ID, horse ID, `left` or `right` decision, and timestamp. A unique constraint on `(user_id, horse_id)` prevents a user from deciding on the same horse twice. Foreign keys cascade when a user or horse is deleted.

The existing `users` and `profiles` tables are unchanged. SQLite initialization is idempotent and adds the new tables to an existing database without removing account/profile data.

## Implementation log

1. Added the horse and swipe schema and an idempotent seed of 50 sample horses.
2. Added a signed-in matching route. It supports breed and age range query filters and skips horses already swiped on by the current account.
3. Added a CSRF-protected swipe form and POST route. Decisions are account-specific and persist across sessions.
4. Added checkpoint 4 placeholder destinations for horse profile and chat links.
5. Added matching navigation, matching page empty states, and README documentation for usage and the schema.
6. Added left/right drag gestures with Hammer.js and Alpine.js; the existing buttons remain as an alternative.

## Checkpoint 3 boundaries

Right swipe records interest only; it does not create a chat or implement mutual matching. Filters are limited to breed and age. Sample records do not include hosted photos, so the page uses a simple horse-mark placeholder. Swipe reset/undo and horse administration are out of scope. The gesture libraries are loaded from public CDNs; if they are unavailable, Like and Pass buttons still work.
