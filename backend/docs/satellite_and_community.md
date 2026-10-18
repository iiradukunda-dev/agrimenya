# Satellite context and farmer community

## Rwanda Space Agency map services

The map overlay uses the publicly reachable Rwanda Space Agency ArcGIS cached
map service:

`https://portal.space.gov.rw/server/rest/services/Hosted/Ortho_Orthomosaic/MapServer`

Its tile endpoint is used as an optional, read-only map layer in the zone
priority map. The service metadata describes an orthomosaic cache in Web
Mercator and currently reports a small extent near Kigali. It does not provide
a capture date in the layer summary reviewed for this integration. Other RSA
portal services include agricultural land-cover feature layers, but those are
classified/vector data rather than raw satellite imagery.

This overlay is for visual orientation only. It is not converted to crop
health, moisture, planting date, or yield signals and does not change a
prediction or priority. Keep that separation until imagery coverage, capture
dates, licensing, field boundaries, cloud/quality masks, and agronomic
validation are established. The map service and its terms can change; confirm
access and attribution with RSA before production use. The agency lists
[contact information](https://www.space.gov.rw/contact) for data enquiries.

The RSA describes its Earth-observation work and agriculture applications on
its [official site](https://www.space.gov.rw/). The portal's public
[Agriculture FeatureServer](https://portal.space.gov.rw/server/rest/services/Hosted/Agriculture/FeatureServer)
exposes classified polygon attributes such as `lulc`; it should not be
mistaken for a time-series imagery API.

## Farmer community pilot

Apply migrations `0009_farmer_community.sql` and `0010_field_observations.sql`
after migrations `0001` through `0008`. Community members register with an email, display name, and password;
accounts currently default to the farmer role. Passwords are stored as scrypt
hashes, sessions expire after one hour, and the community API checks account
status and session version on each request. Rate limits apply to registration,
login, posts, comments, and reports. Users can report posts or comments;
administrators review reports and hide, restore, or soft-delete content from
the Admin panel. Community tables have RLS enabled and no public policies;
only the backend service role accesses them.

This is a development pilot. Email ownership and farmer/organization roles are
not yet verified, and account recovery is not yet available. The interface says
so explicitly. Before public launch, add verified email or phone recovery,
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
