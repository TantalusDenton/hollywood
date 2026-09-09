from __future__ import annotations

from ..base import VideoProvider, VideoProviderCapabilities


class WanVideoProvider(VideoProvider):
    """Shared WAN defaults. Backends may override capabilities to match a deployed model."""

    def get_capabilities(self) -> VideoProviderCapabilities:
        return VideoProviderCapabilities(
            text_to_video=True, image_to_video=True, first_frame=True, last_frame=False,
            reference_images=True, audio=False, max_duration_seconds=10,
            supported_resolutions=("480p", "720p"), supported_aspect_ratios=("16:9", "9:16"),
        )
