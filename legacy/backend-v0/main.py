from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="KOYASH API",
    description="MVP v0 API foundation for KOYASH skincare recommendation service.",
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "koyash-api",
        "version": "0.0.1",
    }


@app.get("/api/sample-products")
def get_sample_products():
    return {
        "products": [
            {
                "id": "sample-001",
                "name": "Gentle Cleanser",
                "brand": "Sample Brand",
                "category": "Cleanser",
                "price_rub": 750,
                "reason": "Matches sensitivity concern and fits the budget segment.",
            },
            {
                "id": "sample-002",
                "name": "Barrier Serum",
                "brand": "Sample Brand",
                "category": "Serum",
                "price_rub": 980,
                "reason": "Supports skin barrier and contains calming active ingredients.",
            },
            {
                "id": "sample-003",
                "name": "Daily SPF 50",
                "brand": "Sample Brand",
                "category": "SPF",
                "price_rub": 890,
                "reason": "Adds daily protection step to the basic routine.",
            },
        ]
    }