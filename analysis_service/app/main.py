from fastapi import FastAPI

app = FastAPI(
    title="Criminal Network Analysis Service",
    description="Member 4 - Network Analysis and AI Service",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "service": "Criminal Network Analysis Service",
        "member": "Member 4",
        "status": "running"
    }