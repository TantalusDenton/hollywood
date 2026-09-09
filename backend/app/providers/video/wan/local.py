from .rest import WanRestProvider


class WanLocalProvider(WanRestProvider):
    """Normalized local server: POST /generate and GET /jobs/{job_id}."""
