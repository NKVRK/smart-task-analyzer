import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .scoring import calculate_scores

LAST_ANALYSIS = {
    "result": None
}

@csrf_exempt
def analyze_tasks(request):
    """
    POST /api/tasks/analyze/
    body: {"tasks": [...], "strategy":"smart_balance", "weights": {...} } 
    """
    if request.method != "POST":
        return HttpResponseBadRequest(json.dumps({"error": "POST required"}), content_type="application/json")
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({"error": "invalid json", "detail": str(e)}), content_type="application/json")

    tasks = payload.get("tasks") or payload
    if isinstance(tasks, dict) and "tasks" in tasks:
        tasks = tasks["tasks"]
    if not isinstance(tasks, list):
        return HttpResponseBadRequest(json.dumps({"error": "tasks must be a list"}), content_type="application/json")

    strategy = payload.get("strategy", "smart_balance")
    weights = payload.get("weights")

    result = calculate_scores(tasks, strategy=strategy, custom_weights=weights)
    LAST_ANALYSIS["result"] = result
    return JsonResponse(result, safe=False)


def suggest_tasks(request):
    """
    GET /api/tasks/suggest/?strategy=...
    Returns top 3 tasks from last analysis (if any).
    """
    if request.method != "GET":
        return HttpResponseBadRequest(json.dumps({"error": "GET required"}), content_type="application/json")

    result = LAST_ANALYSIS.get("result")
    if not result:
        return JsonResponse({"error": "No analyzed tasks found. POST to /api/tasks/analyze/ first."}, status=400)
    
    top3 = result.get("analyzed_tasks", [])[:3]
    return JsonResponse({"suggested_tasks": top3, "meta": result.get("meta")})
