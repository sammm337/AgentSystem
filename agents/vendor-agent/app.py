from flask import Flask, request, jsonify
from models import CreateListingPayload, CreateEventPayload

from shared.utils.mongo_client import db
from shared.schemas.listing_schema import ListingBase, EventBase, MediaItem
from services.stt import get_stt_service
from services.llm import OllamaWrapper
from services.image_service import ImageEnhancer
from services.vector_client import QdrantClientWrapper
from services.mq import MQProducer
import uuid, datetime, os, traceback

app = Flask(__name__)

# Upload folder
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize services
stt = get_stt_service()
llm = OllamaWrapper()
imgsvc = ImageEnhancer()
vec = QdrantClientWrapper()
mq = MQProducer()

def persist_and_publish(obj: dict, collection: str, vector_collection: str, embedding: list, routing_key: str):
    obj["id"] = obj.get("id") or str(uuid.uuid4())
    now = datetime.datetime.utcnow()
    # Store ISO format string for JSON serialization everywhere
    obj["created_at"] = now.isoformat()
    db[collection].insert_one(obj)
    # Create clean payload without _id for Qdrant (MongoDB adds _id after insert_one)
    payload_for_vec = {k: v for k, v in obj.items() if k != "_id"}
    vec.upsert(vector_collection, [{"id": obj["id"], "vector": embedding, "payload": payload_for_vec}])
    mq.publish("hyperlocal", routing_key, payload_for_vec)
    # Return clean copy without MongoDB _id for JSON response
    clean_obj = {k: v for k, v in obj.items() if k != "_id"}
    return clean_obj

@app.route("/agent/vendor/create-listing", methods=["POST"])
def create_listing():
    try:
        metadata = request.form.get("metadata")
        if not metadata:
            return jsonify({"error": "metadata form field required"}), 400
        payload = CreateListingPayload(**eval(metadata))  # convert string to dict

        media_docs = []
        merged_text = []
        all_tags = []

        # Handle uploaded files
        files = request.files.getlist("media_files")
        for f in files:
            filename = os.path.join(UPLOAD_FOLDER, f.filename)
            f.save(filename)

            try:
                if f.filename.lower().endswith(('.wav', '.mp3', '.ogg')):
                    print(f"[AssemblyAISTT] Transcribing: {f.filename}")
                    txt = stt.transcribe(filename)
                    print(f"[AssemblyAISTT] Raw transcription: {txt}")
                    
                    # Translate Hindi/Marathi to English using LLM
                    # Check if text is in non-Latin script (Hindi/Marathi)
                    if any('\u0900' <= c <= '\u097F' for c in txt):  # Devanagari script range
                        print(f"[Translation] Detected non-English text, translating to English...")
                        translate_prompt = f"Translate the following text to English, keeping the meaning exact. Do not add any extra details:\n\n{txt}"
                        english_txt = llm.generate(translate_prompt)
                        print(f"[Translation] English translation: {english_txt}")
                        txt = english_txt
                    
                    mq.publish("hyperlocal", "transcription.completed", {"source": f.filename, "text": txt})
                    # Expand text and generate tags
                    expand = llm.generate(f"Summarize in 2-3 sentences: {txt}")
                    print(f"[LLM] Summary: {expand}")
                    merged_text.append(expand)
                    # Use JSON mode for structured tag extraction
                    tags_prompt = f'Extract 5-10 key topics from this text. Return ONLY a JSON array of strings, no other text. Example: ["topic1", "topic2"]. Text: {txt}'
                    tags_txt = llm.generate(tags_prompt, json_mode=True)
                    print(f"[LLM] Raw tags response: {tags_txt}")
                    # Parse JSON tags
                    try:
                        import json as json_module
                        tags = json_module.loads(tags_txt)
                        if not isinstance(tags, list):
                            tags = [t.strip() for t in tags_txt.split(",") if t.strip() and len(t.strip()) > 1]
                    except:
                        # Fallback to comma-separated parsing
                        tags = [t.strip() for t in tags_txt.split(",") if t.strip() and len(t.strip()) > 1]
                    # Filter out very long tags that are likely prompt artifacts
                    tags = [t for t in tags if len(t) < 50 and len(t) > 1]
                    print(f"[Tags] Cleaned tags: {tags}")
                    all_tags.extend(tags)
                    media_docs.append({"path": filename, "kind": "audio", "tags": tags})
                else:
                    res = imgsvc.enhance(filename)
                    mq.publish("hyperlocal", "image.processed", {"source": f.filename, "enhanced": res["enhanced_path"], "tags": res["tags"]})
                    # Generate additional tags via LLM with JSON mode
                    tags_prompt = f'Extract 5-10 key topics from these image tags. Return ONLY a JSON array of strings. Tags: {" ".join(res["tags"])}'
                    tags_txt = llm.generate(tags_prompt, json_mode=True)
                    try:
                        import json as json_module
                        tags = json_module.loads(tags_txt)
                        if not isinstance(tags, list):
                            tags = [t.strip() for t in tags_txt.split(",") if t.strip() and len(t.strip()) > 1]
                    except:
                        tags = [t.strip() for t in tags_txt.split(",") if t.strip() and len(t.strip()) > 1]
                    tags = [t for t in tags if len(t) < 50 and len(t) > 1]
                    all_tags.extend(tags)
                    media_docs.append({"path": res["enhanced_path"], "kind": "image", "tags": tags})
                    merged_text.append(" ".join(res["tags"]))
            except Exception as media_err:
                print(f"[Error] Processing media {f.filename}: {media_err}")
                traceback.print_exc()
                media_docs.append({"path": filename, "kind": "unknown", "tags": []})
                merged_text.append("")

        all_tags = list(set(all_tags))  # remove duplicates

        # Create a faithful summary instead of creative marketing copy
        if merged_text and any(t.strip() for t in merged_text):
            notes = " ".join([t for t in merged_text if t.strip()])
            description = llm.generate(f"Write a brief, factual description (3-4 sentences) based on these notes: {notes}")
        else:
            description = "Cozy homestay in a great location."
        
        title = payload.title or (all_tags[0] if all_tags else "Cozy stay")

        listing = ListingBase(
            vendor_id=payload.vendor_id,
            title=title,
            description=description,
            price=payload.price,
            location=payload.location,
            tags=all_tags,
            media=[MediaItem(**m) for m in media_docs]
        ).dict()

        txt_for_embed = f"{listing['title']} {listing['description']} {' '.join(listing['tags'])}"
        embed_response = llm.embed([txt_for_embed])

        # Parse embedding safely
        try:
            if isinstance(embed_response, list) and len(embed_response) > 0:
                embed = embed_response[0] if isinstance(embed_response[0], list) else embed_response
            else:
                embed = embed_response.get("embeddings", [embed_response])[0] if isinstance(embed_response, dict) else embed_response[0]
        except Exception as embed_err:
            print(f"[Error] Embedding parse failed: {embed_err}")
            traceback.print_exc()
            embed = [0.0] * 1536  # fallback

        persisted = persist_and_publish(listing, "listings", "vendor_listings_vectors", embed, "listing.created")
        return jsonify({"status": "ok", "listing": persisted}), 201

    except Exception as e:
        print("[Error] create_listing failed:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/agent/vendor/create-event", methods=["POST"])
def create_event():
    try:
        payload = CreateEventPayload(**request.json)
        media_docs = []
        merged_text = []
        all_tags = []

        for path in payload.media_files:
            if path.lower().endswith(('.wav', '.mp3', '.ogg')):
                txt = stt.transcribe(path)
                mq.publish("hyperlocal", "transcription.completed", {"source": path, "text": txt})
                expanded = llm.generate(f"Expand and translate to English: {txt}")
                merged_text.append(expanded)
                tags_txt = llm.generate(f"Generate 5–10 tags (comma-separated) from this text: {txt}")
                tags = [t.strip() for t in tags_txt.split(",") if t.strip()]
                all_tags.extend(tags)
                media_docs.append({"path": path, "kind": "audio", "tags": tags})
            else:
                res = imgsvc.enhance(path)
                mq.publish("hyperlocal", "image.processed", {"source": path, "enhanced": res["enhanced_path"], "tags": res["tags"]})
                tags_txt = llm.generate(f"Generate 5–10 tags (comma-separated) from these image tags: {' '.join(res['tags'])}")
                tags = [t.strip() for t in tags_txt.split(",") if t.strip()]
                all_tags.extend(tags)
                media_docs.append({"path": res["enhanced_path"], "kind": "image", "tags": tags})
                merged_text.append(" ".join(res["tags"]))

        all_tags = list(set(all_tags))  # remove duplicates

        description = llm.generate(f"Create marketing blurb for event '{payload.title}' using these notes: {merged_text}")
        event = EventBase(
            agency_id=payload.agency_id,
            title=payload.title,
            description=description,
            datetime=payload.datetime,
            location=payload.location,
            price=payload.price,
            tags=all_tags,
            media=[MediaItem(**m) for m in media_docs]
        ).dict()

        txt_for_embed = f"{event['title']} {event['description']} {' '.join(event['tags'])}"
        embed_response = llm.embed([txt_for_embed])
        
        if isinstance(embed_response, list) and len(embed_response) > 0:
            embed = embed_response[0] if isinstance(embed_response[0], list) else embed_response
        else:
            embed = embed_response.get("embeddings", [embed_response])[0] if isinstance(embed_response, dict) else embed_response[0]

        persisted = persist_and_publish(event, "events", "agency_events_vectors", embed, "event.created")
        return jsonify({"status": "ok", "event": persisted}), 201

    except Exception as e:
        print("[Error] create_event failed:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/agent/vendor/update-metadata", methods=["POST"])
def update_metadata():
    try:
        data = request.json
        col = data.get("collection")
        obj_id = data.get("id")
        update = data.get("update")
        
        if not col or not obj_id:
            return jsonify({"error": "collection and id required"}), 400
        
        result = db[col].update_one({"id": obj_id}, {"$set": update})
        if result.matched_count == 0:
            return jsonify({"error": "Object not found"}), 404
        
        mq.publish("hyperlocal", "metadata.updated", {"collection": col, "id": obj_id, "update": update})
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("[Error] update_metadata failed:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=False)
