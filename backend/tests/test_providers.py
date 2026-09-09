import respx
from httpx import Response

from app.providers.video.google import GoogleVideoProvider
from app.providers.video.wan.rest import WanRestProvider


def test_google_veo_31_advertises_last_frame_capability_without_network():
    provider = object.__new__(GoogleVideoProvider)
    provider.model = "veo-3.1-generate-preview"
    capabilities = provider.get_capabilities()
    assert capabilities.first_frame is True
    assert capabilities.last_frame is True


async def test_wan_rest_adapter_posts_normalized_generation_contract():
    provider = WanRestProvider("https://wan.example", "secret", "wan-model")
    with respx.mock(base_url="https://wan.example") as router:
        route = router.post("/generate").mock(return_value=Response(200, json={"job_id": "job-1"}))
        result = await provider.submit_normalized_request({"prompt": "A crane shot", "duration": 6})
    await provider.client.aclose()
    assert route.called
    assert result["job_id"] == "job-1"
