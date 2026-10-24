# Satellite imagery and farmer community

## Rwanda Space Agency map services

The application currently does not show a satellite imagery overlay. The
publicly reachable Rwanda Space Agency ArcGIS cached map service previously
reviewed was an orthomosaic cache with a small extent near Kigali and no capture
date in its layer summary. That is insufficient for reliable nationwide,
seasonal crop monitoring, so it was removed from the farmer/planner map rather
than presented as useful coverage. The app does not derive crop health,
moisture, planting dates, or yield from satellite imagery.

Before adding imagery again, obtain a documented national/seasonal source with
capture dates, licensing and attribution, suitable resolution, cloud/quality
masks, and a validated method tied to crop and field boundaries. Treat any
future imagery as dated evidence with provenance, not as a decorative layer or
an automatic diagnosis. Contact the [Rwanda Space Agency](https://www.space.gov.rw/contact)
to confirm current access and terms.

The RSA describes its Earth-observation work and agriculture applications on
its [official site](https://www.space.gov.rw/). The portal's public
[Agriculture FeatureServer](https://portal.space.gov.rw/server/rest/services/Hosted/Agriculture/FeatureServer)
exposes classified polygon attributes such as `lulc`; it should not be
mistaken for a time-series imagery API.

## Farmer community pilot

Apply migrations `0009_farmer_community.sql`, `0010_field_observations.sql`,
and `0011_community_unique_usernames.sql`
after migrations `0001` through `0008`. Community members register with a unique username, email, and password;
accounts currently default to the farmer role. Passwords are stored as scrypt
hashes, sessions expire after one hour, and the community API checks account
status and session version on each request. Rate limits apply to registration,
login, posts, comments, and reports. Users can report posts or comments;
administrators review reports and hide, restore, or soft-delete content from
the Admin panel. Community tables have RLS enabled and no public policies;
only the backend service role accesses them.

This is a development pilot. Email ownership and farmer/organization roles are
not yet verified. Password recovery uses a signed, expiring link delivered by
SMTP in deployed environments and an on-screen link in local development.
Account session versioning makes a reset link single-use. Set
`COMMUNITY_PASSWORD_RESET_URL` to the public Community page URL for deployment.
Before public launch, add verified email or phone ownership,
verified organization roles where required, a published community standard and
privacy notice, and durable abuse throttling/monitoring at the API edge. Never
present a peer post as an official extension recommendation.

Migration `0010` adds a compact field observation flow with district, crop,
observation date, notes, and an optional photo. Reports are stored in the
existing `field_reports` table with the community author and a private Storage
object path. The migration creates a private `community-field-reports` bucket;
the API compresses and re-encodes uploads as JPEG and returns 15-minute signed
image URLs to signed-in community members. Keep this farmer submitted data
clearly labeled: it is not an official NISR observation and must never be mixed
into the NISR yield baseline imports. Field symptom reports can contribute to
the separate live field-risk context.

The community page has an explicit English/Kinyarwanda switch, responsive
phone-sized forms, larger buttons, and client-side photo compression for lower
bandwidth. The optional photo can be omitted on a slow connection.

Migration `0011_community_unique_usernames.sql` makes the existing community
handle unique case-insensitively and limits new handles to 3–30 lowercase
letters, digits, or underscores. Email addresses were already unique
case-insensitively in migration `0009`.
