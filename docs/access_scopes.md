# Agri-Menya access scopes

Agri-Menya supports public exploration, individual farmer participation, and privileged administration. The interface should not imply that a public visitor has signed in or can save private work.

| Scope | Intended access | Enforcement |
| --- | --- | --- |
| Public visitor | Rwanda administrative map, published district crop evidence, public dashboard and read-only pages | Read endpoints do not require a farmer login. No zone creation or community posting. |
| Farmer Community account | Public features plus verified, signed-in community participation and mapped farm/site creation | Community endpoints require an active, verified account session. Creating a zone requires a signed Community bearer token. |
| Administrator | Public features plus administration and moderation, and mapped site creation | Admin endpoints require a signed administrator session and active account. |

Agricultural Segmentation is public to explore. It uses Rwanda-only 2022 administrative boundaries for district, sector, and cell lookup. Only a signed-in farmer or administrator can save a farm/site pin or indicative outline. A pin is an ordinary WGS84 location; a drawn outline is farmer-provided and must not be described as a surveyed or legal parcel boundary. District-level evidence is statistical context and is not a claim about an individual farm.

Do not move secrets into browser-visible code. The production deployment must keep environment-level API credentials private and must use signed account sessions for Community and Administrator actions. The local development `require_user` behavior is intentionally more permissive for existing integration workflows; production role checks remain the security boundary.

When adding a page or endpoint, keep public reads separate from farmer writes and administrative actions. Give each new route an explicit dependency and show the corresponding sign-in guidance in the interface.
