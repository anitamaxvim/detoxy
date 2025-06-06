import time
from pathlib import Path

import litserve as ls
import torch
from litserve import Request, Response

from detoxy.model.config import SERVER_CONFIG
from detoxy.model.module import ToxicClassifier


class SimpleLitAPI(ls.LitAPI):
    def setup(
        self,
        device: str,
        ckpt_path: str | Path = SERVER_CONFIG.finetuned,
        precision: str = SERVER_CONFIG.precision,
    ) -> None:
        self.lit_module = ToxicClassifier.load_from_checkpoint(ckpt_path).to(device)
        self.lit_module.to(device).to(precision)
        self.lit_module.eval()

        self.labels = self.lit_module.labels

    async def decode_request(self, request: Request):
        return request["input"]

    async def predict(self, input: str) -> torch.Tensor:
        return self.lit_module.predict_step(input)

    async def encode_response(self, output: torch.Tensor) -> Response:
        return {label: prob.item() for label, prob in zip(self.labels, output)}


class SimpleLogger(ls.Logger):
    def process(self, key, value):
        print(f"{key}: {value:.2f}", flush=True)


class PredictionTimeLogger(ls.Callback):
    def on_before_predict(self, lit_api):
        t0 = time.perf_counter()
        self._start_time = t0

    def on_after_predict(self, lit_api):
        t1 = time.perf_counter()
        elapsed = t1 - self._start_time
        lit_api.log("prediction_time", elapsed)


if __name__ == "__main__":
    api = SimpleLitAPI(enable_async=True)
    callbacks = [PredictionTimeLogger()]
    loggers = [SimpleLogger()]

    server = ls.LitServer(
        api,
        # callbacks=callbacks,
        # loggers=loggers,
        accelerator=SERVER_CONFIG.accelerator,
        devices=SERVER_CONFIG.devices,
        timeout=SERVER_CONFIG.timeout,
        track_requests=SERVER_CONFIG.track_requests,
    )
    server.run(port=8000, generate_client_file=SERVER_CONFIG.generate_client_file)
