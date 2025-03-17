#!/usr/bin/env python3
"""
Example script demonstrating the enhanced memory tool in OpenManus.
This script shows how to use the memory system for context persistence across tasks,
including the new vector embedding-based semantic search capabilities.
"""

import sys
import json
import os
import time
from datetime import datetime
from pprint import pprint

# Add the parent directory to sys.path to import OpenManus modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.tools.memory_tool import MemoryTool
except ImportError as e:
    print(f"Error importing MemoryTool: {e}")
    print("Please install the required dependencies:")
    print("  pip install faiss-cpu sentence-transformers nltk")
    sys.exit(1)

def main():
    print("OpenManus Enhanced Memory Tool Demo")
    print("=" * 60)
    
    # Initialize memory tools for comparison
    try:
        # Vector-based memory (enhanced)
        vector_memory = MemoryTool(
            memory_path="data/vector_memory",
            use_vectors=True,
            vector_db_path="data/vector_memory_db",
            model_name="all-MiniLM-L6-v2",  # Small, fast model
            chunk_size=256,  # Smaller chunk size for demo
            chunk_overlap=50
        )
        
        # Text-based memory (original)
        text_memory = MemoryTool(
            memory_path="data/text_memory",
            use_vectors=False
        )
        
        has_vector_search = True
        print("Vector-based semantic search enabled!")
    except Exception as e:
        print(f"Warning: Could not initialize vector-based memory: {e}")
        print("Running with text-based search only")
        vector_memory = None
        text_memory = MemoryTool(memory_path="data/memory")
        has_vector_search = False
    
    # Use vector memory if available, otherwise fall back to text memory
    memory = vector_memory if has_vector_search else text_memory
    namespace = "conversation_history"
    
    print("\n1. Storing user preferences in memory...")
    user_preferences = {
        "travel": {
            "preferred_airlines": ["ANA", "Singapore Airlines", "Delta"],
            "hotel_stars": 4,
            "interests": ["local cuisine", "museums", "nature"]
        },
        "name": "Alex",
        "location": "San Francisco"
    }
    
    memory.store(
        content="User preferences for trip planning",
        metadata=user_preferences,
        namespace="user_data"
    )
    print("User preferences stored.")
    
    print("\n2. Simulating a conversation with memory persistence...")
    
    # Store a series of conversation messages
    conversations = [
        {"speaker": "User", "content": "I'd like to plan a trip to Tokyo for 3 days", "type": "user_message"},
        {"speaker": "Agent", "content": "I'll help you plan a 3-day trip to Tokyo. What types of activities are you interested in?", "type": "agent_message"},
        {"speaker": "User", "content": "I'm interested in cultural sites, good food, and maybe shopping", "type": "user_message"},
        {"speaker": "Agent", "content": "Great! Tokyo has amazing cultural sites like Sensoji Temple and Meiji Shrine. For food, you might enjoy trying sushi at Tsukiji Outer Market and ramen in Tokyo Station's Ramen Street. Popular shopping areas include Shibuya, Ginza, and Akihabara for electronics.", "type": "agent_message"},
        {"speaker": "User", "content": "That sounds good. I'd like to visit the Ghibli Museum too.", "type": "user_message"},
        {"speaker": "Agent", "content": "The Ghibli Museum is a wonderful choice! It's located in Mitaka and requires advance ticket purchase. I'll include it in your itinerary. Would you like recommendations for hotels in Tokyo?", "type": "agent_message"},
        {"speaker": "User", "content": "Yes, I'd prefer to stay somewhere central with easy access to trains.", "type": "user_message"}
    ]
    
    # Store all conversation messages
    for message in conversations:
        memory.store(
            content=message["content"],
            metadata={"type": message["type"], "timestamp": datetime.now().isoformat()},
            namespace=namespace
        )
        print(f"{message['speaker']}: {message['content']}")
    
    # 3. Demonstrate long-form content chunking
    print("\n3. Demonstrating memory chunking for long text...")
    
    # Long description that will be automatically chunked
    tokyo_info = """
    Tokyo is Japan's capital and largest city. It's a bustling metropolis that combines ultramodern and traditional elements, from neon-lit skyscrapers to historic temples. The city is famous for its vibrant culture, cutting-edge technology, exquisite cuisine, and efficient public transportation system.
    
    Some of Tokyo's most popular attractions include:
    
    - Sensoji Temple: Tokyo's oldest temple, located in Asakusa
    - Tokyo Skytree: One of the world's tallest structures with observation decks
    - Meiji Shrine: A peaceful Shinto shrine surrounded by a forest in the heart of Tokyo
    - Shibuya Crossing: The world's busiest pedestrian crossing
    - Tsukiji Outer Market: Famous for fresh seafood and sushi restaurants
    - Shinjuku Gyoen National Garden: Beautiful park with Japanese, English, and French gardens
    - Akihabara: Electronics and anime/manga district
    - Tokyo Disneyland and DisneySea: Popular theme parks
    
    Tokyo's cuisine is world-renowned, with more Michelin-starred restaurants than any other city. Visitors can enjoy everything from high-end sushi to street food like takoyaki (octopus balls) and yakitori (grilled chicken skewers). The city's ramen shops, izakayas (Japanese pubs), and department store food halls are culinary destinations in themselves.
    
    Shopping in Tokyo offers everything from high-end luxury brands in Ginza to trendy fashion in Shibuya and Harajuku. For electronics, visit Akihabara, while Nakamise Shopping Street in Asakusa offers traditional souvenirs. Don't miss the 100-yen shops (similar to dollar stores) for quirky Japanese goods.
    
    Tokyo's efficient public transportation system makes getting around easy. The JR Yamanote Line loops around central Tokyo, connecting major stations. The subway system reaches most tourist destinations. The prepaid Suica or Pasmo cards can be used on trains, subways, and buses.
    
    For day trips from Tokyo, consider visiting Kamakura with its Great Buddha, Nikko with its elaborate shrines, or Hakone for hot springs and views of Mount Fuji when the weather is clear.
    """
    
    print("Storing comprehensive Tokyo information...")
    memory.store(
        content=tokyo_info,
        metadata={"type": "city_guide", "city": "Tokyo", "country": "Japan"},
        namespace="travel_guides"
    )
    
    if has_vector_search:
        print(f"\nContent automatically split into {len(vector_memory._chunk_text(tokyo_info))} chunks for better semantic search")
    
    # 4. Demonstrate semantic search vs. text search
    if has_vector_search:
        print("\n4. Comparing semantic search vs. text-based search...")
        
        # Store additional travel guides for comparison
        kyoto_info = """
        Kyoto, once the capital of Japan, is a city on the island of Honshu. It's famous for its numerous classical Buddhist temples, as well as gardens, imperial palaces, Shinto shrines and traditional wooden houses. It's also known for formal traditions such as kaiseki dining and geisha entertainers.
        
        The city has over 1,600 Buddhist temples and 400 Shinto shrines, including the famous Kinkaku-ji (Golden Pavilion), Kiyomizu-dera Temple, and Fushimi Inari Shrine with its thousands of vermilion torii gates. 
        
        Kyoto is considered the cultural heart of Japan and is one of the best preserved cities in the country, having been spared from much of the destruction of World War II. It was the seat of the imperial court for more than a thousand years, and to this day remains an important cultural center.
        
        The cuisine of Kyoto, known as Kyo-ryori, is highly refined, emphasizing the natural flavors of fresh, seasonal ingredients. The city is known for its traditional kaiseki ryori (multi-course dinners), shojin ryori (Buddhist vegetarian cuisine), and yudofu (hot tofu).
        
        Visitors to Kyoto can experience traditional culture by participating in a tea ceremony, staying in a ryokan (traditional inn), or spotting geiko (Kyoto's geisha) in the Gion district.
        """
        
        osaka_info = """
        Osaka is Japan's third largest city and a commercial powerhouse, known for its modern architecture, vibrant nightlife, and amazing street food. The city has a reputation for being more laid-back and outgoing than Tokyo.
        
        Top attractions include Osaka Castle, which played a major role in the unification of Japan during the 16th century; Dotonbori, a bustling entertainment district with bright neon lights and a variety of restaurants; and Universal Studios Japan, a popular theme park.
        
        Osaka is widely known as "Japan's kitchen" and is a paradise for food lovers. Must-try local specialties include takoyaki (octopus balls), okonomiyaki (savory pancakes), kushikatsu (deep-fried skewered meat and vegetables), and kitsune udon (udon noodles with fried tofu).
        
        The city is centered around two main areas: Kita (North) with its business district and Minami (South) which is the entertainment hub. Osaka's people are known for their humor and openness, making it a friendly city for visitors.
        
        Shopping options range from high-end department stores like Takashimaya to the 2.6km-long Tenjinbashisuji Shopping Street, the longest shopping arcade in Japan. For electronics, Den Den Town rivals Tokyo's Akihabara, often with better prices.
        """
        
        text_memory.store(content=kyoto_info, metadata={"type": "city_guide", "city": "Kyoto"}, namespace="travel_guides")
        text_memory.store(content=osaka_info, metadata={"type": "city_guide", "city": "Osaka"}, namespace="travel_guides")
        vector_memory.store(content=kyoto_info, metadata={"type": "city_guide", "city": "Kyoto"}, namespace="travel_guides")
        vector_memory.store(content=osaka_info, metadata={"type": "city_guide", "city": "Osaka"}, namespace="travel_guides")
        
        # Semantic search queries
        search_queries = [
            "where to see beautiful gardens and temples",
            "best places for shopping electronics in Japan",
            "Japanese food recommendations and local cuisine"
        ]
        
        for query in search_queries:
            print(f"\nQuery: '{query}'")
            
            # Text-based search
            text_results = text_memory.search(query, namespace="travel_guides", k=2)
            print("\nText-based search results:")
            for i, result in enumerate(text_results):
                print(f"  Result {i+1} - Score: {result.get('relevance_score', 'N/A'):.2f}")
                print(f"  City: {result['metadata'].get('city', 'Unknown')}")
                print(f"  Content excerpt: {result['content'][:150]}...\n")
            
            # Vector-based search
            vector_results = vector_memory.search(query, namespace="travel_guides", k=2)
            print("\nSemantic search results:")
            for i, result in enumerate(vector_results):
                print(f"  Result {i+1} - Score: {result.get('relevance_score', 'N/A'):.2f}")
                print(f"  City: {result['metadata'].get('city', 'Unknown')}")
                print(f"  Matching chunks: {result.get('matching_chunks', 'N/A')}")
                print(f"  Content excerpt: {result['content'][:150]}...\n")
    
    # 5. Demonstrate contextual retrieval for conversational AI
    print("\n5. Demonstrating contextual retrieval for conversational AI...")
    
    # New user query requiring context from past conversation
    current_query = "How many days should I plan for the Ghibli Museum?"
    print(f"User: {current_query}")
    
    # Retrieve relevant context using search
    context_results = memory.search(
        "Ghibli Museum Tokyo",
        namespace=namespace,
        k=3
    )
    
    print("\nRetrieved context for answering:")
    for i, result in enumerate(context_results):
        speaker = "User" if result["metadata"]["type"] == "user_message" else "Agent"
        print(f"  {i+1}. {speaker}: {result['content']}")
        if has_vector_search:
            print(f"     Relevance: {result.get('relevance_score', 'N/A'):.2f}")
    
    # 6. Update memory with new information
    print("\n6. Updating memories with new information...")
    
    # Store task progress in memory
    memory.store(
        content="Tokyo Trip Planning",
        metadata={
            "status": "in_progress",
            "progress": 0.3,
            "completed_steps": ["gather user preferences", "research top attractions"],
            "pending_steps": ["create daily itinerary", "suggest accommodations", "finalize plan"]
        },
        namespace="tasks",
        memory_id="tokyo_trip_plan"
    )
    
    # Update the task progress
    updated_metadata = {
        "progress": 0.6,
        "completed_steps": ["gather user preferences", "research top attractions", "create daily itinerary", "book Ghibli Museum tickets"],
        "pending_steps": ["suggest accommodations", "finalize plan"]
    }
    
    memory.update(
        memory_id="tokyo_trip_plan",
        metadata=updated_metadata,
        namespace="tasks"
    )
    
    # Verify update
    updated_task = memory.get("tokyo_trip_plan", "tasks")
    print("\nUpdated task status:")
    print(f"  Progress: {updated_task['metadata']['progress'] * 100:.0f}%")
    print(f"  Completed steps: {', '.join(updated_task['metadata']['completed_steps'])}")
    print(f"  Pending steps: {', '.join(updated_task['metadata']['pending_steps'])}")
    
    # 7. Show how to use memory for personalization
    print("\n7. Using memory for personalization...")
    
    # Retrieve user preferences
    user_prefs = memory.search("preferences interests", "user_data")
    
    if user_prefs:
        user_data = user_prefs[0]
        user_name = user_data["metadata"].get("name", "there")
        user_interests = user_data["metadata"].get("travel", {}).get("interests", [])
        
        print(f"\nPersonalized response for {user_name}:")
        print(f"Based on your interests in {', '.join(user_interests)}, here's a customized Tokyo itinerary:")
        print("  Day 1: Start with the Sensoji Temple in Asakusa to experience local culture")
        print("  Day 2: Visit the Ghibli Museum (tickets pre-booked) and explore local food options")
        print("  Day 3: Shopping day in Shibuya and Harajuku, with evening at a local izakaya")
    
    # Clean up test data
    if input("\nDelete test data? (y/n): ").lower() == 'y':
        if has_vector_search:
            vector_memory.clear_namespace("travel_guides")
            vector_memory.clear_namespace("conversation_history")
            vector_memory.clear_namespace("user_data")
            vector_memory.clear_namespace("tasks")
        text_memory.clear_namespace("travel_guides")
        text_memory.clear_namespace("conversation_history")
        text_memory.clear_namespace("user_data")
        text_memory.clear_namespace("tasks")
        print("Test data deleted.")
    
    print("\nEnhanced memory demo complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()