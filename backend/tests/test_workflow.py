from app.graph.workflow import MovieWorkflow, WorkflowRuntime


class Repository:
    def __init__(self): self.saved = []
    async def save_state(self, project_id, state): self.saved.append((project_id, state))


class Pipeline:
    async def emit(self, *args, **kwargs): pass
    async def analyze_story(self, state): return {"title": "Film", "story_analysis": {"title": "Film"}}
    async def extract_characters(self, state): return {"characters": []}
    async def generate_character_references(self, state): return {}
    async def break_story_into_scenes(self, state): return {"scenes": []}
    async def break_scenes_into_shots(self, state): return {"shots": []}
    async def generate_shot_prompts(self, state): return {}
    async def generate_keyframes(self, state): return {}
    async def generate_video_clips(self, state): return {}
    async def validate_clips(self, state): return {}
    async def assemble_movie(self, state): return {"final_movie_path": "movie.mp4"}


async def test_workflow_keeps_required_node_order_and_completes(tmp_path):
    from langgraph.checkpoint.memory import MemorySaver
    repo = Repository()
    workflow = MovieWorkflow(WorkflowRuntime(repository=repo, pipeline=Pipeline(), checkpointer=MemorySaver()))
    result = await workflow.run({"project_id": "00000000-0000-0000-0000-000000000001", "original_prompt": "A story", "generation_settings": {"director_mode": False}, "current_stage": "created", "progress": 0, "status": "pending"})
    assert result["status"] == "completed"
    assert result["final_movie_path"] == "movie.mp4"
    assert repo.saved[-1][1]["current_stage"] == "assemble_movie"
