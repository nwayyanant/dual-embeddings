import httpx
import asyncio
import json

async def debug_search_scores():
    """Debug script to check search scores"""
    search_url = "http://localhost:8083"
    
    queries = ["hello", "meditation", "dharma"]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in queries:
            print(f"\n{'='*80}")
            print(f"Query: '{query}'")
            print(f"{'='*80}")
            
            response = await client.post(
                f"{search_url}/search",
                json={"query": query, "top_k": 5, "alpha": 0.5}
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                print(f"\nTotal results: {len(results)}")
                print(f"Language: {data.get('query_lang')}")
                print(f"Alpha: {data.get('alpha')}\n")
                
                for i, result in enumerate(results, 1):
                    score = result.get("score", 0)
                    score_type = result.get("score_type", "unknown")
                    doc_id = result.get("doc_id", "N/A")
                    snippet = result.get("snippet", "")[:100]
                    
                    print(f"[{i}] Score: {score:.15f} (type: {score_type})")
                    print(f"    Doc: {doc_id}")
                    print(f"    Snippet: {snippet}...")
                    print()
            else:
                print(f"Error: {response.status_code}")
                print(response.text)

if __name__ == "__main__":
    asyncio.run(debug_search_scores())