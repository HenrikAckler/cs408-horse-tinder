# Checkpoint 3 Implementation Notes

## Project plan scope

Checkpoint 3 adds generated sample profiles, basic matching filters, and left/right swipes. Full profile and chat views remain checkpoint 4 features; the matching page links to clearly labeled placeholders for those destinations.

## Database changes

`schema.sql` defines three tables:

- `logindata` contains credentials for real user accounts.
- `profiledata` contains every matchable profile in the same format. Real users have a linked login row; the 50 sample profiles do not. There is no horse/user type field. Stable `seed_key` values make sample rows safe to seed again at startup.
- `swipes` contains the real user's ID, the matched profile's ID, a `left` or `right` decision, and timestamp. A unique constraint on `(user_id, profile_id)` prevents a user from deciding on the same profile twice. Foreign keys cascade when a login or profile is deleted.

Matching queries all `profiledata` rows except the signed-in user's own profile, regardless of whether a row is linked to a login. The breed filter uses the same matchable set. The local SQLite database was reset as requested; users need to register again. Initialization and sample profile seeding remain idempotent.

## Implementation log

1. Added the profile and swipe schema and an idempotent seed of 50 sample profiles.
2. Added a signed-in matching route. It supports breed and age range query filters and skips horses already swiped on by the current account.
3. Added a CSRF-protected swipe form and POST route. Decisions are account-specific and persist across sessions.
4. Added checkpoint 4 placeholder destinations for profile and chat links.
5. Added matching navigation, matching page empty states, and README documentation for usage and the schema.
6. Added left/right drag gestures with Hammer.js and Alpine.js; the existing buttons remain as an alternative.
7. Unified user and sample profiles in `profiledata`, moved credentials to `logindata`, and changed swipes to reference profile IDs. Matching treats every other profile the same.

## Checkpoint 3 boundaries

Right swipe records interest only; it does not create a chat or implement mutual matching. Filters are limited to breed and age. Sample records do not include hosted photos, so the page uses a simple horse-mark placeholder. Swipe reset/undo and profile administration are out of scope. The gesture libraries are loaded from public CDNs; if they are unavailable, Like and Pass buttons still work.
