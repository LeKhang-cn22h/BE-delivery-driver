import json
from collections import defaultdict
from typing import List, Dict, Any, Tuple

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio

app = FastAPI(
    title="Analytics API - Enhanced",
    description="Route analysis & post office location suggestions",
    version="2.0.0"
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
def extract_location_pairs() -> List[Dict[str, Any]]:
    """
    Extract pickup-delivery location point pairs from MinIO
    Returns list of orders with their location pairs
    """
    orders_data = []

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

            payload = data.get("payload", {})

            # ✅ FIX 1: Get pickup location correctly
            pickup_location = payload.get("pickup_address", "")
            pickup_area = payload.get("pickup_area_code", "")

            # ✅ FIX 2: Extract delivery locations correctly
            delivery_locations = []
            for detail in payload.get("order_details", []):
                delivery_location = detail.get("address_detail", "")
                delivery_area = detail.get("area_code", "")

                # Get coordinates
                location_obj = detail.get("location", {})
                lat = location_obj.get("lat") if isinstance(location_obj, dict) else None
                lng = location_obj.get("lng") if isinstance(location_obj, dict) else None

                if delivery_location:
                    delivery_locations.append({
                        "location": delivery_location,
                        "area_code": delivery_area,
                        "lat": lat,
                        "lng": lng
                    })

            # Only add if we have both pickup and delivery
            if pickup_location and delivery_locations:
                orders_data.append({
                    "pickup_location": pickup_location,
                    "pickup_area": pickup_area,
                    "deliveries": delivery_locations,
                    "order_id": payload.get("id")
                })

        except Exception as e:
            print(f"Error processing order: {e}")
            continue
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()

    return orders_data


def analyze_location_pairs(
        orders_data: List[Dict[str, Any]],
        min_support: float = 0.01
) -> List[Dict[str, Any]]:
    """
    Analyze location point pairs that frequently appear together
    Calculate support, confidence, and lift for each pair
    """
    total_orders = len(orders_data)
    if total_orders == 0:
        return []

    # Count individual locations
    pickup_counts: Dict[str, int] = defaultdict(int)
    delivery_counts: Dict[str, int] = defaultdict(int)

    # ✅ FIX 3: Count DIRECTIONAL pairs (pickup → delivery)
    pair_counts: Dict[Tuple[str, str], Dict] = defaultdict(lambda: {
        "count": 0,
        "pickup_area": "",
        "delivery_area": ""
    })

    for order in orders_data:
        pickup = order["pickup_location"]
        pickup_area = order["pickup_area"]
        deliveries = order["deliveries"]

        # Count pickup location
        pickup_counts[pickup] += 1

        # Count delivery locations
        for delivery in deliveries:
            delivery_loc = delivery["location"]
            delivery_area = delivery.get("area_code", "")

            delivery_counts[delivery_loc] += 1

            # ✅ FIX: Don't sort - keep directionality!
            pair_key = (pickup, delivery_loc)
            pair_counts[pair_key]["count"] += 1
            pair_counts[pair_key]["pickup_area"] = pickup_area
            pair_counts[pair_key]["delivery_area"] = delivery_area

    # Calculate metrics for each pair
    results = []

    for pair, data in pair_counts.items():
        count = data["count"]
        pickup_loc, delivery_loc = pair  # ← Now ordered!

        # Support: Tỷ lệ đơn hàng có route này
        support = count / total_orders

        if support < min_support:
            continue

        # Support của từng location
        support_pickup = pickup_counts[pickup_loc] / total_orders
        support_delivery = delivery_counts[delivery_loc] / total_orders

        # Confidence: P(delivery | pickup)
        confidence = support / support_pickup if support_pickup > 0 else 0

        # Lift: Đo mức độ phụ thuộc
        expected = support_pickup * support_delivery
        lift = support / expected if expected > 0 else 0

        # Prediction
        if lift > 2.0 and confidence > 0.7:
            prediction = "RẤT THƯỜNG xuất hiện cùng nhau - Nên mở bưu cục ngay"
        elif lift > 1.5 and confidence > 0.5:
            prediction = "THƯỜNG xuất hiện cùng nhau - Nên cân nhắc mở bưu cục"
        elif lift > 1.2:
            prediction = "Có xu hướng xuất hiện cùng nhau"
        else:
            prediction = "Xuất hiện độc lập với nhau"

        results.append({
            "pickup_location": pickup_loc,
            "delivery_location": delivery_loc,
            "pickup_area": data["pickup_area"],
            "delivery_area": data["delivery_area"],
            "total_orders": count,
            "support": round(support, 4),
            "confidence": round(confidence, 4),
            "lift": round(lift, 3),
            "prediction": prediction,
            "suggested_office_location": delivery_loc  # Suggest at delivery location
        })

    # Sort by confidence (most predictable routes first)
    return sorted(results, key=lambda x: x["confidence"], reverse=True)


def interpret_lift(lift: float) -> str:
    """Interpret lift value"""
    if lift > 1.5:
        return "Rất thường xuất hiện cùng nhau"
    elif lift > 1.2:
        return "Thường xuất hiện cùng nhau"
    elif lift > 0.8:
        return "Xuất hiện độc lập"
    else:
        return "Ít xuất hiện cùng nhau"


def suggest_post_office_locations(
        location_pairs: List[Dict[str, Any]],
        top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Suggest new post office locations based on frequently paired locations
    """
    suggestions = []

    for i, pair in enumerate(location_pairs[:top_n], 1):
        # ✅ FIX: Use correct field names from analyze_location_pairs()
        pickup_loc = pair["pickup_location"]
        delivery_loc = pair["delivery_location"]
        lift = pair["lift"]
        support = pair["support"]
        confidence = pair["confidence"]  # ← Changed from confidence_avg
        count = pair["total_orders"]  # ← Changed from count
        prediction = pair["prediction"]

        # Calculate priority score
        priority_score = (
                support * 40 +  # Tần suất xuất hiện
                confidence * 30 +  # Độ tin cậy
                min(lift, 3) / 3 * 30  # Độ phụ thuộc (cap tại 3)
        )

        # Determine urgency based on lift and confidence
        if lift > 2.0 and confidence > 0.7:
            urgency = "Rất cao"
            color = "🔴"
            action = "NÊN MỞ BƯU CỤC NGAY"
        elif lift > 1.5 and confidence > 0.5:
            urgency = "Cao"
            color = "🟠"
            action = "Nên cân nhắc mở bưu cục"
        elif lift > 1.2:
            urgency = "Trung bình"
            color = "🟡"
            action = "Có thể xem xét"
        else:
            urgency = "Thấp"
            color = "🟢"
            action = "Ưu tiên thấp"

        # Generate suggestion
        suggestion = {
            "rank": i,
            "location": delivery_loc,  # Main suggestion location
            "location_short": delivery_loc[:60] + "..." if len(delivery_loc) > 60 else delivery_loc,
            "area": pair.get("delivery_area", ""),
            "statistics": {
                "orders_count": count,
                "support": f"{support * 100:.2f}%",
                "confidence": f"{confidence * 100:.2f}%",
                "lift": lift,
                "interpretation": interpret_lift(lift)
            },
            "priority_score": round(priority_score, 2),
            "priority_level": urgency.lower().replace(" ", "_"),  # very_high, high, medium, low
            "priority_label": f"{color} {urgency}",
            "recommendation": action,
            "top_routes": [
                {
                    "from": pickup_loc[:50] + "..." if len(pickup_loc) > 50 else pickup_loc,
                    "to": delivery_loc[:50] + "..." if len(delivery_loc) > 50 else delivery_loc,
                    "lift": lift,
                    "confidence": confidence
                }
            ],
            "avg_lift": lift,
            "avg_confidence": confidence,
            "total_orders": count
        }

        suggestions.append(suggestion)

    return suggestions


def generate_reason_for_locations(loc1: str, loc2: str, count: int, lift: float, confidence: float) -> str:
    """Generate reason for suggestion based on locations"""
    reasons = []

    if lift > 2.0:
        reasons.append(f"Hai điểm này có mối liên hệ RẤT MẠNH (Lift={lift:.2f})")
    elif lift > 1.5:
        reasons.append(f"Hai điểm xuất hiện cùng nhau rất thường xuyên (Lift={lift:.2f})")
    elif lift > 1.2:
        reasons.append(f"Hai điểm có xu hướng xuất hiện cùng nhau (Lift={lift:.2f})")

    if confidence > 0.7:
        reasons.append(f"Độ tin cậy rất cao {confidence * 100:.1f}%")
    elif confidence > 0.5:
        reasons.append(f"Độ tin cậy cao {confidence * 100:.1f}%")

    reasons.append(f"Đã xử lý {count} đơn hàng giữa 2 điểm này")

    if lift > 2.0 and confidence > 0.7:
        reasons.append("⚠️ ĐÂY LÀ CẶP ĐIỂM ƯU TIÊN CAO NHẤT")

    return ". ".join(reasons) + "."


def generate_benefit(count: int, support: float, lift: float) -> str:
    """Generate expected benefit"""
    benefits = []

    # Estimate time savings
    time_saved = int(count * 0.3 * 15)  # Giả sử tiết kiệm 15 phút/đơn cho 30% đơn
    benefits.append(f"Tiết kiệm ước tính {time_saved} phút/tháng")

    # Estimate cost reduction
    if lift > 1.5:
        benefits.append("Giảm 20-30% chi phí vận chuyển giữa 2 khu vực")
    elif lift > 1.2:
        benefits.append("Giảm 10-20% chi phí vận chuyển giữa 2 khu vực")

    # Service improvement
    if support > 0.05:
        benefits.append(f"Cải thiện thời gian giao hàng cho {support * 100:.1f}% đơn hàng")

    return ". ".join(benefits) + "."


# =========================
# API ENDPOINTS
# =========================
@app.get("/api/location-pairs", summary="Phân tích các cặp điểm xuất hiện cùng nhau")
def get_location_pairs(
        min_support: float = Query(0.01, ge=0.001, le=1, description="Ngưỡng support tối thiểu"),
        limit: int = Query(50, ge=1, le=200, description="Số lượng cặp tối đa")
):
    """
    Phân tích các cặp điểm (pickup-delivery locations) xuất hiện cùng nhau
    """
    orders_data = extract_location_pairs()

    if not orders_data:
        return {
            "pairs": [],
            "total_orders": 0,
            "message": "Không có dữ liệu đơn hàng"
        }

    pairs = analyze_location_pairs(orders_data, min_support)

    return {
        "pairs": pairs[:limit],
        "total_pairs": len(pairs),
        "total_orders": len(orders_data),
        "params": {
            "min_support": min_support,
            "limit": limit
        }
    }


@app.get("/api/post-office-suggestions", summary="Gợi ý vị trí mở bưu cục dựa trên cặp điểm")
def get_post_office_suggestions(
        min_support: float = Query(0.02, ge=0.001, le=1, description="Ngưỡng support tối thiểu"),
        top_n: int = Query(10, ge=1, le=50, description="Số lượng gợi ý")
):
    """
    Gợi ý vị trí mở bưu cục mới dựa trên phân tích các cặp điểm
    """
    orders_data = extract_location_pairs()

    if not orders_data:
        return {
            "suggestions": [],
            "total_orders": 0,
            "message": "Không có dữ liệu để phân tích"
        }

    pairs = analyze_location_pairs(orders_data, min_support)
    suggestions = suggest_post_office_locations(pairs, top_n)

    return {
        "suggestions": suggestions,
        "total_analyzed_pairs": len(pairs),
        "total_orders": len(orders_data)
    }


@app.get("/api/location-hotspots", summary="Xác định các điểm HOT (nhiều đơn nhất)")
def get_location_hotspots(
        top_n: int = Query(20, ge=5, le=100, description="Số lượng điểm top")
):
    """
    Xác định các điểm có lượng đơn hàng nhiều nhất
    """
    orders_data = extract_location_pairs()

    if not orders_data:
        return {
            "hotspots": [],
            "message": "Không có dữ liệu"
        }

    # Count locations
    location_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "pickup_count": 0,
        "delivery_count": 0,
        "total": 0,
        "area": ""
    })

    for order in orders_data:
        pickup = order["pickup_location"]
        pickup_area = order["pickup_area"]

        location_stats[pickup]["pickup_count"] += 1
        location_stats[pickup]["total"] += 1
        location_stats[pickup]["area"] = pickup_area

        for delivery in order["deliveries"]:
            delivery_loc = delivery["location"]
            delivery_area = delivery.get("area_code", "")

            location_stats[delivery_loc]["delivery_count"] += 1
            location_stats[delivery_loc]["total"] += 1
            location_stats[delivery_loc]["area"] = delivery_area

    # Convert to list and sort
    hotspots = []
    for location, stats in location_stats.items():
        total = stats["total"]
        pickup_count = stats["pickup_count"]
        delivery_count = stats["delivery_count"]

        # Determine category
        if pickup_count > delivery_count * 1.5:
            category = "pickup_heavy"
        elif delivery_count > pickup_count * 1.5:
            category = "delivery_heavy"
        else:
            category = "balanced"

        hotspots.append({
            "location": location,
            "pickup_count": pickup_count,
            "delivery_count": delivery_count,
            "total_orders": total,
            "pickup_ratio": round(pickup_count / total, 2) if total > 0 else 0,
            "delivery_ratio": round(delivery_count / total, 2) if total > 0 else 0,
            "category": category
        })

    hotspots = sorted(hotspots, key=lambda x: x["total_orders"], reverse=True)

    return {
        "hotspots": hotspots[:top_n],
        "total_locations": len(hotspots),
        "total_orders": len(orders_data)
    }


@app.get("/health", summary="Health check")
def health():
    try:
        minio.bucket_exists(BUCKET_NAME)
        return {"status": "healthy", "service": "analytics_service_enhanced"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)