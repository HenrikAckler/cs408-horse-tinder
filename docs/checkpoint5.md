# Checkpoint 5: Horse Feed

## Scope

The feed is a signed-in, read-only page at `/feed`. It shows 100 sample posts, newest first, with text and optional photos. Search filters titles, text, and author names. There is no post creation or feed interaction.

## Data and seed behavior

- `feed_posts` stores the post title, text, optional image path, author profile, and creation timestamp.
- Posts reference `profiledata`, so seeded horse profiles and real user profiles use the same author relationship. Seed posts use the existing 50 sample profiles and do not create fake login accounts.
- Stable seed keys and `INSERT OR IGNORE` make the post seed safe to run at each startup.
- Sample timestamps span the previous 100 days to make post-age ordering visible.

## Images

Fourteen compressed, distinct Unsplash photos are bundled under `static/images/feed/`. A seeded-random selection chooses one post from each of 14 time slices, spreading the photos throughout the timeline without reusing any image. Posts store paths relative to Flask's static directory; they do not store image blobs or require a third-party image host at runtime. Source links are listed beside the images and a credit appears below the feed.
