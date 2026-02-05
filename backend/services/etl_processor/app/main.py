import json
from collections import defaultdict
from typing import List, Dict, Any
from itertools import combinations

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio

app = FastAPI(
    title="Analytics API",
    description="Route analysis & area statistics service",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MinIO setup
minio = Minio(
    "minio:9000",
    access_key="admin",
    secret_key="admin123",
    secure=False
)

BUCKET_NAME = "datalake"


# =========================
# UTILITIES
# =========================
def extract_routes() -> List[set]:
    """Extract pickup->delivery pairs from MinIO"""
    transactions: List[set] = []

    objects = minio.list_objects(
        BUCKET_NAME,
        prefix="orders/",
        recursive=True
    )

    for obj in objects:
        if not obj.object_name.endswith(".json"):
            continue

        try:
            response = minio.get_object(BUCKET_NAME, obj.object_name)
            data = json.loads(response.read())

            pickup = data["payload"]["pickup_area_code"]
            routes = set()

            for detail in data["payload"]["order_details"]:
                delivery = detail["area_code"]
                routes.add(f"{pickup}->{delivery}")

            if routes:
                transactions.append(routes)

        except Exception as e:
            continue
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()

    return transactions


def apriori_analysis(
        transactions: List[set],
        min_support: float = 0.01,
        min_confidence: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Apriori algorithm for route association rules
    Finds frequent route pairs and generates rules
    """
    total = len(transactions)
    if total == 0:
        return []

    # Step 1: Count single items (L1)
    item_counts: Dict[str, int] = defaultdict(int)
    for transaction in transactions:
        for item in transaction:
            item_counts[item] += 1

    # Filter by min_support
    frequent_1 = {
        item: count / total
        for item, count in item_counts.items()
        if (count / total) >= min_support
    }

    # Step 2: Generate candidate pairs (C2)
    frequent_items = list(frequent_1.keys())
    pair_counts: Dict[frozenset, int] = defaultdict(int)

    for transaction in transactions:
        # Find all pairs in this transaction
        items_in_txn = [item for item in transaction if item in frequent_1]
        for pair in combinations(items_in_txn, 2):
            pair_counts[frozenset(pair)] += 1

    # Filter pairs by min_support (L2)
    frequent_2 = {
        pair: count / total
        for pair, count in pair_counts.items()
        if (count / total) >= min_support
    }

    # Step 3: Generate association rules
    rules = []

    for pair, support in frequent_2.items():
        items = list(pair)

        # Generate both directions: A -> B and B -> A
        for i in range(2):
            antecedent = items[i]
            consequent = items[1 - i]

            # Confidence = Support(A,B) / Support(A)
            confidence = support / frequent_1[antecedent]

            if confidence >= min_confidence:
                # Lift = Confidence / Support(B)
                lift = confidence / frequent_1[consequent]

                rules.append({
                    "from": antecedent,
                    "to": consequent,
                    "support": round(support, 4),
                    "confidence": round(confidence, 4),
                    "lift": round(lift, 3),
                    "count": pair_counts[pair]
                })

    # Sort by confidence, then support
    return sorted(rules, key=lambda x: (x["confidence"], x["support"]), reverse=True)


# =========================
# ROUTES
# =========================
@app.get("/api/route-analysis", summary="Phân tích tuyến đường (Apriori)")
def route_analysis(
        min_support: float = Query(0.01, ge=0, le=1, description="Minimum support threshold"),
        min_confidence: float = Query(0.1, ge=0, le=1, description="Minimum confidence threshold"),
        limit: int = Query(50, ge=1, le=500, description="Max number of rules to return")
):
    """
    Analyze route associations using Apriori algorithm
    Returns rules like: "If route A->B, then route C->D appears X% of the time"
    """
    transactions = extract_routes()
    rules = apriori_analysis(transactions, min_support, min_confidence)

    return {
        "rules": rules[:limit],
        "total_transactions": len(transactions),
        "total_rules": len(rules),
        "params": {
            "min_support": min_support,
            "min_confidence": min_confidence
        }
    }


@app.get("/api/area-stats", summary="Thống kê pickup / delivery area")
def area_stats(top_n: int = Query(10, ge=1, le=100)):
    """
    Get statistics for most common pickup and delivery areas
    """
    transactions = extract_routes()

    pickup_counts = defaultdict(int)
    delivery_counts = defaultdict(int)

    for transaction in transactions:
        for route in transaction:
            try:
                pickup, delivery = route.split("->")
                pickup_counts[pickup] += 1
                delivery_counts[delivery] += 1
            except ValueError:
                continue  # Skip malformed routes

    return {
        "pickup_areas": [
            {"area": k, "count": v}
            for k, v in sorted(
                pickup_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_n]
        ],
        "delivery_areas": [
            {"area": k, "count": v}
            for k, v in sorted(
                delivery_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_n]
        ],
        "total_transactions": len(transactions)
    }


@app.get("/health", summary="Health check")
def health():
    try:
        # Test MinIO connection
        minio.bucket_exists(BUCKET_NAME)
        return {"status": "healthy", "service": "analytics_service"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}