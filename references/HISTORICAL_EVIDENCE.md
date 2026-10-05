# Historical Evidence Protocol

## 1. Evidence hierarchy

Use the strongest available evidence, but judge relevance as well as authority.

### Tier A — primary/direct
- archival documents, institutional records, contemporaneous newspapers
- dated photographs with known provenance
- letters, diaries, speeches, minutes, enrollment/administrative records
- maps, architectural plans, catalogs, yearbooks
- oral history from a direct participant/witness, clearly identified

### Tier B — authoritative secondary
- peer-reviewed scholarship
- university/museum/archive histories with citations
- scholarly monographs
- official chronologies that expose sources

### Tier C — useful contextual secondary
- reputable journalism
- edited commemorative volumes
- curated exhibitions
- biographies without full archival apparatus

### Tier D — leads only
- unsourced webpages, social posts, captions copied across sites
- AI summaries
- fan pages

Tier D can point to a source; it should not normally anchor a contested historical claim.

## 2. Claim ledger discipline

Every narration-level historical claim should receive an ID such as `E001`.

Minimum fields:
- exact claim
- date/place/person involved
- source title/URL/file/page
- evidence tier
- verification status
- exact support or paraphrase note
- visual material linked to claim
- safe wording

Example statuses:
- VERIFIED — directly supported
- SUPPORTED_INFERENCE — evidence supports an inference but not an explicit statement
- CREATIVE_RECONSTRUCTION — invented connective tissue/visualization, not fact
- UNRESOLVED — conflicting or insufficient evidence
- REJECTED — contradicted or too weak

## 3. Wording by certainty

Match language to evidence strength.

Strong evidence:
- “1906年，……”
- “档案显示……”

Inference:
- “从现有资料看……”
- “这可能意味着……”
- keep inference out of omniscient narration when unnecessary

Reconstruction:
- production note: “根据现存照片与同期资料进行视觉复原”
- do not write a fabricated inner monologue as an authentic quotation

## 4. Quotations

Never invent a quotation for dramatic effect.

For every quote record:
- speaker
- exact wording
- source
- date/context
- whether modernization/translation is used

If exact wording cannot be verified, paraphrase and remove quotation marks.

## 5. Old photographs

Before treating a photo as evidence, verify when possible:
- subject identity
- location
- approximate/exact date
- photographer/source collection
- whether caption was added later
- whether image is cropped, mirrored, retouched, or miscaptioned

Do not use a generic period photo to “prove” a specific event.

## 6. Architecture and place reconstruction

Lock known geometry before style:
- façade proportions
- number/shape of openings
- roofline
- signage
- gate/road relationship
- surrounding structures/vegetation only where supported

Separate:
- known from image/plan
- inferred from same site/era
- invented for cinematic completeness

## 7. People and reenactment

When depicting identifiable historical people:
- use documented age/appearance/clothing only when known
- avoid precise facial claims from insufficient material
- do not fabricate criminal, political, romantic, medical, or other sensitive conduct
- label dramatized dialogue/reenactment in production notes

## 8. AI visual reconstruction

AI output is a visualization layer, not a source.

For each generated historical shot record:
- evidence IDs used
- reference images
- invariant features
- uncertain features
- stylistic choices
- whether disclosure/title card is needed

Good prompt architecture:
1. scene function
2. verified historical constraints
3. subject/object invariants
4. camera/lens/movement
5. light/weather
6. rendering texture
7. forbidden mutations/anachronisms

## 9. Conflict resolution

If sources disagree:
- state the conflict in the ledger
- privilege primary or more methodologically transparent evidence
- do not silently choose the more cinematic version
- if nonessential, cut the disputed detail
- if essential, write the uncertainty into the film or seek stronger evidence
