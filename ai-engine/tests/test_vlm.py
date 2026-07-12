"""Tests for the VLM module (Module 2).

Run fast unit tests only (no model download, safe for quick iteration):
    pytest -m "not integration"

Run everything, including real CLIP downloads (needs network + a few hundred MB):
    pytest

Run only the integration tests:
    pytest -m integration
"""
import pytest
import torch
from PIL import Image

from src.vlm import CLIPVLM, VLMConfig, VLMLoadError

# ---------------------------------------------------------------------------
# Fast unit tests — no model download, no network. These should always pass
# instantly and are what you'd run on every save during development.
# ---------------------------------------------------------------------------


def test_vlm_config_defaults():
    config = VLMConfig()
    assert config.model_name == "openai/clip-vit-base-patch32"
    assert config.freeze_weights is True
    assert config.device is None


def test_vlm_config_resolved_device_explicit():
    config = VLMConfig(device="cpu")
    assert config.resolved_device() == "cpu"


def test_vlm_config_resolved_device_auto():
    config = VLMConfig()
    # Whatever the environment provides, this must not raise and must be "cpu" or "cuda".
    assert config.resolved_device() in ("cpu", "cuda")


# ---------------------------------------------------------------------------
# Integration tests — these actually load CLIP from Hugging Face Hub. Run these
# in Colab or any environment with network access, before considering the
# module complete.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def clip_vlm():
    """Load CLIP once and reuse across every integration test in this file —
    downloading/loading weights repeatedly for every test would be slow."""
    return CLIPVLM(VLMConfig(device="cpu"))  # CPU keeps this portable across CI runners


@pytest.mark.integration
def test_clip_loads_successfully(clip_vlm):
    assert clip_vlm.model is not None
    assert clip_vlm.processor is not None


@pytest.mark.integration
def test_encode_image_shape_and_normalization(clip_vlm):
    dummy_image = Image.new("RGB", (224, 224), color=(128, 128, 128))
    pixel_values = clip_vlm.preprocess_image(dummy_image)
    embeds = clip_vlm.encode_image(pixel_values)

    assert embeds.shape == (1, 512)
    # encode_image must return L2-normalized vectors
    assert torch.allclose(embeds.norm(dim=-1), torch.tensor([1.0]), atol=1e-4)


@pytest.mark.integration
def test_encode_text_shape_and_normalization(clip_vlm):
    embeds = clip_vlm.encode_text(["a photo of a dog"])

    assert embeds.shape == (1, 512)
    assert torch.allclose(embeds.norm(dim=-1), torch.tensor([1.0]), atol=1e-4)


@pytest.mark.integration
def test_encode_text_batch(clip_vlm):
    embeds = clip_vlm.encode_text(["a dog", "a cat", "a car"])
    assert embeds.shape == (3, 512)


@pytest.mark.integration
def test_similarity_range_and_shape(clip_vlm):
    dummy_image = Image.new("RGB", (224, 224), color=(200, 50, 50))
    pixel_values = clip_vlm.preprocess_image(dummy_image)
    image_embeds = clip_vlm.encode_image(pixel_values)
    text_embeds = clip_vlm.encode_text(["a red image", "a blue image"])

    sim = clip_vlm.similarity(image_embeds, text_embeds)

    assert sim.shape == (1, 2)
    # cosine similarity must be in [-1, 1] (small tolerance for float error)
    assert torch.all(sim >= -1.01) and torch.all(sim <= 1.01)


@pytest.mark.integration
def test_vision_attentions_shape(clip_vlm):
    dummy_image = Image.new("RGB", (224, 224), color=(128, 128, 128))
    pixel_values = clip_vlm.preprocess_image(dummy_image)
    attentions = clip_vlm.get_vision_attentions(pixel_values)

    num_layers = clip_vlm.model.config.vision_config.num_hidden_layers
    assert len(attentions) == num_layers
    # each layer's attention tensor: [batch, heads, tokens, tokens]
    assert attentions[0].dim() == 4
    assert attentions[0].shape[0] == 1  # batch size


@pytest.mark.integration
def test_load_error_on_invalid_model_name():
    with pytest.raises(VLMLoadError):
        CLIPVLM(VLMConfig(model_name="not-a-real-model/does-not-exist", device="cpu"))
