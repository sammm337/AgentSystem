from flask import Flask, request, jsonify
from models import SearchRequest, RecommendRequest, ItineraryRequest, MessageRequest
from services.llm import OllamaLocal
from services.vector_client import search_listings_vector, search_events_vector
from shared.utils.mongo_client import db
from services.mq import MQConsumer
from services.reranker import rerank
import threading

app = Flask(__name__)
llm = OllamaLocal()

# Background subscriber to MQ events to update local caches / analytics
def process_event(routing_key, payload):
    # Example: update user's recommendations, cache new listing/event in Mongo's search cache
    print("MQ event", routing_key)

def start_mq():
    consumer = MQConsumer()
    consumer.start(process_event)

threading.Thread(target=start_mq, daemon=True).start()

@app.route("/agent/traveler/search", methods=["POST"])
def search():
    try:
        req = SearchRequest(**request.json)
        # step 1: vector search with query string (not embedding)
        if req.mode == "via_vendor":
            raw_results = search_listings_vector(req.query, top_k=10)
        else:
            raw_results = search_events_vector(req.query, top_k=10)
        
        # step 2: parse results
        raw = raw_results if isinstance(raw_results, dict) else {"points": raw_results}
        # step 3: parse and filter results
        results = []
        points = raw.get("result", raw.get("points", []))[:10]
        for hit in points:
            payload = hit.get("payload", {})
            results.append({
                "id": hit.get("id"),
                "score": hit.get("score", 0),
                "payload": payload
            })
        
        # step 4: rerank
        reranked = rerank(results, req.query)
        return jsonify({"results": reranked})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/agent/traveler/recommend", methods=["POST"])
def recommend():
    try:
        req = RecommendRequest(**request.json)
        history = list(db.user_history.find({"user_id": req.user_id}).sort("timestamp", -1).limit(10))
        
        if history:
            last_query = history[0].get("query", "")
            vendor = search_listings_vector(last_query, top_k=req.limit)
            agency = search_events_vector(last_query, top_k=req.limit)
            out = {"vendor": vendor, "agency": agency}
        else:
            out = {"vendor": [], "agency": []}
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/agent/traveler/itinerary", methods=["POST"])
def itinerary():
    try:
        req = ItineraryRequest(**request.json)
        items = []
        for id_ in req.items:
            doc = db.listings.find_one({"id": id_}) or db.events.find_one({"id": id_})
            if doc:
                items.append(f"{doc.get('title')} - {doc.get('description')}")
        
        if not items:
            return jsonify({"error": "No items found"}), 404
        
        prompt = f"Create a {req.days}-day itinerary for a traveler using these items:\n" + "\n".join(items)
        plan = llm.generate(prompt)
        return jsonify({"itinerary": plan})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/agent/traveler/message", methods=["POST"])
def message():
    try:
        req = MessageRequest(**request.json)
        doc = db.listings.find_one({"id": req.target_id}) or db.events.find_one({"id": req.target_id})
        if not doc:
            return jsonify({"error": "Target item not found"}), 404
        
        context = req.context or ""
        prompt = f"Write a polite negotiation message from user {req.user_id} to the owner about {doc.get('title','item')} trying to get a discount. Context: {context}"
        msg = llm.generate(prompt)
        return jsonify({"message": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)
