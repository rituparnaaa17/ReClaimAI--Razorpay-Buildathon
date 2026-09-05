from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import transactions, recovery, agent, analytics, webhooks, batch
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="ReclaimAI API",
    description="AI-powered revenue recovery platform — Razorpay Buildathon Track 3",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(recovery.router, prefix="/api/recovery", tags=["Recovery"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(batch.router, prefix="/api/recovery", tags=["Batch"])


@app.get("/")
def root():
    return {"product": "ReclaimAI", "version": "1.0.0", "status": "operational", "track": "AI Revenue Recovery"}


@app.get("/health")
def health():
    return {"status": "ok"}
