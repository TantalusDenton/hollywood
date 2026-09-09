from ...models.schemas import ContinuityPackage, Shot, StoryAnalysis


def start_frame_prompt(shot: Shot, analysis: StoryAnalysis, continuity: ContinuityPackage) -> str:
    previous = f" Previous shot visual continuity: {continuity.previous_shot_end_frame}." if continuity.previous_shot_end_frame else ""
    return f"""Start frame for shot {shot.sequence_number}: {shot.beginning_state}. {shot.description}
Location: {shot.location}. Lighting: {shot.lighting}. Characters: {'; '.join(continuity.character_descriptions)}.
Props: {', '.join(continuity.important_props)}. {analysis.style_bible.visual_style}.{previous}"""


def end_frame_prompt(shot: Shot, analysis: StoryAnalysis, continuity: ContinuityPackage) -> str:
    return f"""End frame for shot {shot.sequence_number}, a logical visual continuation of the start frame:
{shot.ending_state}. Maintain identity, costume, location, props, lighting, and {analysis.style_bible.visual_style}.
Characters: {'; '.join(continuity.character_descriptions)}."""
