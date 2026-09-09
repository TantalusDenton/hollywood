from .rest import WanRestProvider


class WanComfyUIProvider(WanRestProvider):
    """Small boundary for mapping Hollywood's normalized request into a ComfyUI workflow."""

    # TODO: install the deployment-specific workflow JSON and override submit_normalized_request.
