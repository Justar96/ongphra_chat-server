import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from langchain_core.tools import BaseTool
from langchain_core.vectorstores import VectorStore
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from app.config.settings import get_settings
from app.utils.fortune_tool import calculate_7n9b_fortune

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

class ToolResult(BaseModel):
    """Model for tool execution results."""
    tool_name: str
    result: Dict[str, Any]
    error: Optional[str] = None
    handled: bool = False
    response: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    modified_message: Optional[str] = None
    
class FortuneTool(BaseTool):
    """LangChain tool for calculating and interpreting fortunes."""
    name: str = "fortune_calculator"
    description: str = "Calculate Thai fortune based on birthdate in YYYY-MM-DD format"
    
    embeddings: Optional[Embeddings] = None
    vector_store: Optional[VectorStore] = None
    interpretation_docs: List[Document] = []
    
    def __init__(self):
        """Initialize the fortune tool with embeddings and vector store."""
        super().__init__()
        try:
            self.embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)
            self._initialize_knowledge_base()
        except Exception as e:
            logger.error(f"Error initializing Fortune Tool: {str(e)}")
            
    def _initialize_knowledge_base(self):
        """Initialize knowledge documents for RAG."""
        try:
            # Define fortune interpretation knowledge
            fortune_knowledge = [
                Document(page_content="High values (5-7) in attana (อัตตะ) indicate strong self-confidence and individuality.", 
                         metadata={"category": "attana", "value_range": "high"}),
                Document(page_content="Low values (1-3) in attana (อัตตะ) suggest humility and group-oriented mindset.", 
                         metadata={"category": "attana", "value_range": "low"}),
                Document(page_content="High values in thana (ธานัง) represent strong financial potential and resource management skills.", 
                         metadata={"category": "thana", "value_range": "high"}),
                Document(page_content="Low values in thana (ธานัง) may indicate challenges with money management.", 
                         metadata={"category": "thana", "value_range": "low"}),
                Document(page_content="High values in putta (ปุตตะ) suggest creativity and strong relationships with children or subordinates.", 
                         metadata={"category": "putta", "value_range": "high"}),
                Document(page_content="When both thana (ธานัง) and kadumpha (กดุมภะ) have high values, financial success is indicated.", 
                         metadata={"category_combo": "thana_kadumpha", "value_range": "high"}),
                Document(page_content="When kamma (กัมมะ) has high values but labha (ลาภะ) has low values, it suggests hard work with delayed rewards.", 
                         metadata={"category_combo": "kamma_labha", "value_range": "mixed"}),
                Document(page_content="When both attana (อัตตะ) and tanu (ตะนุ) have high values, it indicates strong self-identity and confidence.", 
                         metadata={"category_combo": "attana_tanu", "value_range": "high"}),
            ]
            
            # Split documents if needed
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            self.interpretation_docs = text_splitter.split_documents(fortune_knowledge)
            
            # Create vector store from documents
            from langchain_community.vectorstores import FAISS
            self.vector_store = FAISS.from_documents(
                documents=self.interpretation_docs,
                embedding=self.embeddings
            )
            
            logger.info(f"Initialized knowledge base with {len(self.interpretation_docs)} documents")
        except Exception as e:
            logger.error(f"Error initializing knowledge base: {str(e)}")
    
    def _run(self, birthdate: str, detail_level: str = "normal") -> Dict[str, Any]:
        """
        Calculate fortune based on birthdate.
        
        Args:
            birthdate: Birthdate in YYYY-MM-DD format
            detail_level: Level of detail (simple, normal, detailed)
            
        Returns:
            Dictionary with fortune calculation and interpretation
        """
        try:
            # Calculate the basic fortune
            fortune_data = calculate_7n9b_fortune(birthdate, detail_level)
            
            # Enrich with RAG if vector store is available
            if self.vector_store:
                enriched_data = self._enrich_with_rag(fortune_data)
                return {"status": "success", "fortune": enriched_data}
            
            return {"status": "success", "fortune": fortune_data}
        except Exception as e:
            logger.error(f"Error running fortune tool: {str(e)}")
            return {
                "status": "error", 
                "message": f"Could not process birthdate: {str(e)}", 
                "original_query": {"birthdate": birthdate, "detail_level": detail_level}
            }
    
    def _enrich_with_rag(self, fortune_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich fortune data with RAG from the knowledge base.
        
        Args:
            fortune_data: The basic fortune calculation results
            
        Returns:
            Enriched fortune data with additional interpretations
        """
        try:
            enriched_data = fortune_data.copy()
            
            # Extract top categories and their values
            top_categories = []
            if "top_categories" in fortune_data:
                for base, data in fortune_data["top_categories"].items():
                    top_categories.append({
                        "category": data["name"],
                        "value": data["value"]
                    })
            
            # Get relevant interpretations for each top category
            rag_interpretations = []
            for category_info in top_categories:
                category = category_info["category"]
                value = category_info["value"]
                value_range = "high" if value >= 5 else "medium" if value >= 3 else "low"
                
                # Query the vector store for this category and value range
                query = f"{category} with {value_range} value"
                try:
                    relevant_docs = self.vector_store.similarity_search(
                        query=query,
                        k=2
                    )
                    
                    # Filter docs manually after search
                    filtered_docs = []
                    for doc in relevant_docs:
                        if (doc.metadata.get("category") == category or 
                            (doc.metadata.get("category_combo") and category in doc.metadata.get("category_combo", ""))):
                            filtered_docs.append(doc)
                    
                    # Add interpretations to the result
                    for doc in filtered_docs:
                        rag_interpretations.append({
                            "category": category,
                            "value": value,
                            "interpretation": doc.page_content,
                            "source": "knowledge_base"
                        })
                except Exception as e:
                    logger.error(f"Error searching vector store: {str(e)}")
            
            # Add RAG interpretations to the result
            if rag_interpretations:
                enriched_data["rag_interpretations"] = rag_interpretations
            
            # Process pairs/combinations for richer data
            if "pairs" in fortune_data and fortune_data["pairs"]:
                # Use the pairs data to enhance the response
                # The pairs from fortune_data already contain headings and meanings
                pairs = fortune_data["pairs"]
                combinations = []
                
                for pair in pairs:
                    combination = {
                        "category": f"{pair.get('thai_name_a', '')}-{pair.get('thai_name_b', '')}",
                        "heading": pair.get("heading", ""),
                        "meaning": pair.get("meaning", ""),
                        "influence": pair.get("influence", "")
                    }
                    combinations.append(combination)
                
                # Add combinations to the enriched data
                enriched_data["combination_interpretations"] = combinations
            
            return enriched_data
        except Exception as e:
            logger.error(f"Error enriching with RAG: {str(e)}")
            return fortune_data

class ToolHandler:
    """Handler for executing tools and processing results."""
    
    def __init__(self):
        """Initialize the tool handler."""
        self.fortune_tool = FortuneTool()
        self.tools = {
            "fortune_calculator": self.fortune_tool
        }
        
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool by name with provided arguments.
        
        Args:
            tool_name: The name of the tool to execute
            **kwargs: Arguments for the tool
            
        Returns:
            ToolResult with the execution results
        """
        try:
            if tool_name not in self.tools:
                return ToolResult(
                    tool_name=tool_name,
                    result={},
                    error=f"Tool not found: {tool_name}"
                )
            
            tool = self.tools[tool_name]
            result = tool.invoke(kwargs)
            
            return ToolResult(
                tool_name=tool_name,
                result=result
            )
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return ToolResult(
                tool_name=tool_name,
                result={},
                error=str(e)
            )

# Create singleton instance
tool_handler = ToolHandler()

# Async dependency function for FastAPI
async def get_tool_handler():
    """Get the tool handler instance as a dependency."""
    return tool_handler 