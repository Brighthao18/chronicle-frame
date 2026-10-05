# Cinematic Visual Synthesis for Archival / AI Historical Films

## 1. Core rule: storyboard sequences, not assets

A historical film is not a slideshow with camera movement. Never design the board by walking through the asset folder one file at a time.

Before individual shots, group the film into 15–35 second **sequences**. Each sequence must have:
- a narrative job
- an emotional turn
- an asset set (usually 3+ relevant assets)
- one primary visual engine
- one secondary visual device
- a camera/path logic
- a sound engine
- an entry transition and exit transition
- one visual payoff

Only after the sequence works should it be split into shots.

## 2. Asset relationship graph

For every useful asset, extract visual primitives rather than treating the whole image as indivisible:
- architecture: arch, roofline, corridor, window, gate axis, staircase
- people: group silhouette, hands, clothing line, gaze direction, posture, crowd density
- documents: date, stamp, handwriting, signature, headline, map contour, seal
- photographs: white border, tear, emulsion texture, perspective, caption area
- geography: route, city label, river/rail/road, campus footprint
- objects: suitcase, book, bell, desk, flag, plaque, register
- typography: exact historical school names or printed phrases

Then connect assets by:
- geometry / shape
- gesture / direction
- chronology
- place
- repeated object
- repeated word/name
- cause and consequence
- emotional contrast

The board should exploit these relationships. A strong sequence often makes two or more sources interact in the same visual construction.

## 3. Visual engines

Choose one primary engine per sequence. Do not repeat the same primary engine in adjacent sequences unless repetition is itself meaningful.

### A. Portal / threshold
Use an opening, gate, window, page, door, dark shape, or photo border as a spatial portal. The camera can move through it into another era or source.

### B. Archival paper world
Place photos, documents, maps, stamps, and handwriting in a coherent shallow 3D paper space. Camera motion reveals relationships, not decoration.

### C. Document-to-world
Begin on a real archival detail (date, place, signature, map line), then let that verified detail become the organizing geometry of the next reconstructed or graphical scene.

### D. Spatial collage / evidence assembly
Fragments from multiple sources assemble into a composite frame: gate geometry, student group, map, caption, and document detail can occupy depth layers while remaining visibly archival.

### E. Geometry match
Match arches, rooflines, human formations, page edges, roads, doorways, or horizon lines across eras. The cut should make the historical relationship visible without VO explaining it.

### F. Motion match / object relay
A line being drawn, a page turning, a suitcase passing, a stamp landing, footsteps, or a door opening continues its screen direction across time.

### G. Time split / parallel frame
Use split frame, layered exposure, or matched compositions to compare two eras simultaneously when the contrast itself is the point.

### H. Map becomes journey
A route should not remain a flat animated line. Let map geometry drive camera direction, reveal archival nodes, become a rail/road/page seam, or terminate in the geometry of the destination image.

### I. Mosaic-to-single-image
Many small evidence fragments converge into one iconic image, or one iconic image fractures into the evidence that explains it.

### J. Occlusion transition
Use a dark gate opening, passing paper edge, foreground pillar, photo border, ink block, smoke/haze only when justified, or moving graphic mask to hide the cut and move through time.

### K. Reconstruction window
Keep the archival image visibly present as evidence while a restrained AI reconstruction expands only beyond or behind it. Never erase the distinction between source and reconstruction.

### L. Rhythmic archival montage
Cut on repeated shapes, poses, words, dates, doors, footsteps, page turns, or musical accents. Rhythm is created by relation, not random speed ramps.

## 4. Anti-slideshow hard constraints

Unless the user explicitly wants a contemplative still-photo essay:

1. Never allow **3 consecutive shots** whose only visual action is slow push, slow pull, pan, tilt, crop, or dissolve over a single still.
2. In any 30-second sequence, at least one shot should contain a meaningful interaction between **2 or more source assets**, or between source evidence and a purposeful graphic/reconstruction layer.
3. A major sequence should normally use **3+ source assets** across its duration when the archive supports it. Do not force irrelevant assets merely to raise the count.
4. No more than roughly **one third of total runtime** should be single-still camera drift unless gravity/observation is the explicit artistic choice.
5. Repeated slow push-ins must be justified by different story functions; changing focal length alone is not variety.
6. A dissolve is not a concept. A transition must express continuity, rupture, comparison, causality, memory, geography, or time.
7. Do not solve lack of motion by hallucinating historical people walking/talking in still photographs. Create motion in camera, depth, graphics, environment, masks, objects, spatial relationships, and transitions instead.

## 5. Camera choreography for AI-only films

Even with only still images, design a camera path through a constructed visual space:
- foreground archival fragment passes lens
- midground hero photo controls evidence
- background map/document/reconstruction provides context
- camera turns or advances to reveal a second source in the same continuous idea
- occlusion or geometry match carries the viewer into the next shot

Use 2.5D/parallax only when layer separation is plausible. Do not create fake depth that bends faces or architecture.

## 6. Historical-photo animation hierarchy

Use the least synthetic method that can deliver the idea:

1. editorial crop / hold / hard cut
2. layered compositing and masks
3. 2.5D parallax from separable planes
4. environmental micro-motion outside protected historical subjects
5. AI expansion/reconstruction clearly treated as reconstruction
6. synthetic human motion only when explicitly chosen and ethically/historically appropriate

The creative goal is cinematic movement, not making every photograph “come alive.”

## 7. Sound is part of the visual engine

Design sound before locking cuts:
- J-cut: next era arrives in sound before image
- L-cut: prior era persists after the cut
- recurring motif: footsteps, page, bell, stamp, train/ship only when historically justified
- silence as rupture
- rhythmic edit driven by documentary sounds or designed foley, not music alone
- distinguish authentic archive audio from designed sound

A transition can be visually simple if the sound bridge carries historical meaning.

## 8. Sequence card template

Before shots, write:

| Sequence | Time | Story turn | Asset set | Primary visual engine | Secondary device | Camera/path | Sound engine | Entry | Exit/payoff | Evidence risk |
|---|---|---|---|---|---|---|---|---|---|---|

Then write a **visual sentence** for the sequence:

> The viewer moves from [source/space A], follows [visual relationship/action], discovers [evidence or contrast], and exits through [motif/transition] into [next state].

If the sentence is merely “show photo A, then photo B, then photo C,” redesign the sequence.

## 9. Shot-level synthesis fields

Add these to each storyboard row:
- `visual_engine`
- `assets_in_frame`
- `layer_interaction`
- `motion_source` (camera / graphic / environment / object / transition / subject)
- `why_this_cut`

These fields force the shot to explain how it becomes video rather than a moving still.

## 10. Creativity without historical deception

High creativity should come from **relationships between verified materials**, not fabricated spectacle.

Good invention:
- turning a real gate opening into a transition matte
- making a verified map route organize camera travel
- compositing multiple real photos into a visible archival collage
- matching a 1909 gate arch to a later gate arch
- letting an exact historical date on a document trigger a cut

Risky invention:
- generating crowds/events that imply documentation that does not exist
- animating a named historical person performing an unverified action
- inserting war/fire/destruction merely to make a rupture dramatic
- reconstructing architecture beyond known evidence and presenting it as certain

Always preserve provenance and label reconstruction in production notes.
