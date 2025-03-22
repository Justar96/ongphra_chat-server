import asyncio
import json
from app.utils.tool_handler import FortuneTool

async def test_rag_directly():
    """Test the RAG functionality directly."""
    print("Testing RAG functionality directly...")
    
    # Create the fortune tool
    fortune_tool = FortuneTool()
    
    # Check if embeddings and vector store are initialized
    if fortune_tool.embeddings:
        print("✅ Embeddings initialized")
    else:
        print("❌ Embeddings not initialized")
    
    if fortune_tool.vector_store:
        print("✅ Vector store initialized")
        print(f"Number of documents in knowledge base: {len(fortune_tool.interpretation_docs)}")
    else:
        print("❌ Vector store not initialized")
    
    # Test the fortune calculation with RAG
    birthdate = "1990-01-15"
    
    try:
        print(f"\nCalculating fortune for birthdate {birthdate}...")
        result = fortune_tool._run(birthdate)
        
        # Check if RAG interpretations were added
        if "fortune" in result:
            fortune_data = result["fortune"]
            rag_interps = fortune_data.get("rag_interpretations", [])
            
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Number of RAG interpretations: {len(rag_interps)}")
            
            # Print the RAG interpretations
            if rag_interps:
                print("\nRAG Interpretations:")
                for i, interp in enumerate(rag_interps, 1):
                    print(f"  {i}. Category: {interp.get('category')} (value: {interp.get('value')})")
                    print(f"     Interpretation: {interp.get('interpretation')}")
                    print(f"     Source: {interp.get('source', 'unknown')}")
                    print()
                
                print("✅ RAG enrichment is working!")
            else:
                print("❌ No RAG interpretations found.")
            
            # Save the result to a file for detailed inspection
            with open("fortune_rag_direct_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print("\nFull result saved to fortune_rag_direct_result.json")
        else:
            print("❌ Fortune data not found in result.")
            print(f"Result: {result}")
    
    except Exception as e:
        print(f"❌ Error testing fortune tool: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_rag_directly()) 