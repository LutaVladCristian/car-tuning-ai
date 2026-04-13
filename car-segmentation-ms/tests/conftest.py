import sys
import types


class FakeSamPredictor:
    def __init__(self, model):
        self.model = model


class FakeYolo:
    def __init__(self, model_path):
        self.model_path = model_path
        self.device = None

    def to(self, device):
        self.device = device
        return self


class FakeSamModel:
    def __init__(self, checkpoint):
        self.checkpoint = checkpoint
        self.device = None

    def to(self, device):
        self.device = device
        return self


def fake_sam_factory(checkpoint):
    return FakeSamModel(checkpoint)


segment_anything = types.ModuleType("segment_anything")
segment_anything.sam_model_registry = {"vit_b": fake_sam_factory}
segment_anything.SamPredictor = FakeSamPredictor

ultralytics = types.ModuleType("ultralytics")
ultralytics.YOLO = FakeYolo

sys.modules.setdefault("segment_anything", segment_anything)
sys.modules.setdefault("ultralytics", ultralytics)
