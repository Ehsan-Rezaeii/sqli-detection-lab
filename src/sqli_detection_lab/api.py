"""Read-only local inference demonstration; no raw-input logging or runtime training."""

from contextlib import asynccontextmanager
from pathlib import Path
from subprocess import SubprocessError

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .artifacts import load_model, verify_freeze
from .io import digest
from .models import scores

WARNING = "Experimental research classifier; not a prevention or WAF control."


class Request(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    value: str = Field(max_length=2048)


class Response(BaseModel):
    label: str
    score: float | None
    model_id: str
    warning: str = WARNING


def create_app(root: Path | None = None):
    root = Path.cwd() if root is None else Path(root)

    @asynccontextmanager
    async def lifespan(app):
        try:
            frozen = verify_freeze(root)
            name = frozen["demo_method"]
            app.state.model = load_model(root, name, frozen)
            app.state.model_id = name + ":" + digest(root / "results/freeze.json")[:16]
            app.state.error = None
        except (OSError, ValueError, KeyError, RuntimeError, SubprocessError) as exc:
            app.state.error = type(exc).__name__
        yield

    app = FastAPI(title="Experimental SQLi-like text classifier", lifespan=lifespan)

    def ready():
        if getattr(app.state, "error", "not_started") is not None:
            raise HTTPException(503, "Trusted frozen local model unavailable")

    @app.get("/health")
    def health():
        ready()
        return {"status": "ok", "model_id": app.state.model_id, "warning": WARNING}

    @app.post("/predict", response_model=Response)
    def predict(request: Request):
        ready()
        score = scores(app.state.model, [request.value])
        label = (
            int(app.state.model.predict([request.value])[0])
            if score is None
            else int(score[0] >= 0.5)
        )
        return Response(
            label="sqli" if label else "norm",
            score=None if score is None else float(score[0]),
            model_id=app.state.model_id,
        )

    return app
