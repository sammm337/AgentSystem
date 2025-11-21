from services.llm import OllamaLocal
import json
import re

llm = OllamaLocal()

def rerank(results: list, query: str) -> list:
    """Rerank results using LLM to improve relevance."""
    if not results:
        return results
    
    try:
        items_text = "\n".join([f"{i+1}. (id={r['id']}) {r['payload'].get('title','')} - {r['payload'].get('description','')}" for i, r in enumerate(results)])
        prompt = f"Rerank the following search results for the search '{query}'. Output ONLY a JSON array of ids in best-to-worst order, like [\"id1\", \"id2\"]:\n{items_text}"
        out = llm.generate(prompt)
        
        # Extract JSON array from LLM response
        json_match = re.search(r'\[.*\]', out, re.DOTALL)
        if json_match:
            try:
                ids_order = json.loads(json_match.group())
                # Create id -> result mapping
                result_map = {r['id']: r for r in results}
                # Reorder by LLM ranking
                reranked = [result_map[id_] for id_ in ids_order if id_ in result_map]
                # Add any missing results at the end
                for r in results:
                    if r['id'] not in ids_order:
                        reranked.append(r)
                return reranked
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"Reranking failed: {e}")
    
    # Fallback: return original order if parsing fails
    return results
