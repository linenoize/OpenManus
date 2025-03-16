#!/usr/bin/env python3
"""
Example script demonstrating the use of the memory tool in OpenManus.
This script shows how to use the memory system for context persistence across tasks.
"""

import sys
import json
import os
import time
from datetime import datetime

# Add the parent directory to sys.path to import OpenManus modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.memory_tool import MemoryTool
from src.client import submit_task, store_memory, search_memories, get_memories

def main():
    print("OpenManus Memory Tool Demo")
    print("=" * 50)
    
    # Initialize a memory tool instance directly
    memory = MemoryTool()
    namespace = "conversation_history"
    
    # 1. Store user preferences in memory
    print("\n1. Storing user preferences...")
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
    
    # 2. Store conversation history
    print("\n2. Simulating a conversation with memory persistence...")
    
    # Initial user query
    user_query = "I'd like to plan a trip to Tokyo for 3 days"
    print(f"\nUser: {user_query}")
    
    # Store the user query in memory
    memory.store(
        content=user_query,
        metadata={"type": "user_message", "timestamp": datetime.now().isoformat()},
        namespace=namespace
    )
    
    # Simulate agent response
    agent_response = "I'll help you plan a 3-day trip to Tokyo. What types of activities are you interested in?"
    print(f"Agent: {agent_response}")
    
    # Store the agent response in memory
    memory.store(
        content=agent_response,
        metadata={"type": "agent_message", "timestamp": datetime.now().isoformat()},
        namespace=namespace
    )
    
    # Follow-up user query
    user_query_2 = "I'm interested in cultural sites, good food, and maybe shopping"
    print(f"\nUser: {user_query_2}")
    
    # Store the follow-up query
    memory.store(
        content=user_query_2,
        metadata={"type": "user_message", "timestamp": datetime.now().isoformat()},
        namespace=namespace
    )
    
    # 3. Retrieve conversation history to maintain context
    print("\n3. Retrieving conversation history...")
    conversations = memory.get_all(namespace)
    
    print(f"\nFound {len(conversations)} messages in conversation history:")
    for i, message in enumerate(conversations):
        speaker = "User" if message["metadata"]["type"] == "user_message" else "Agent"
        print(f"  {i+1}. {speaker}: {message['content']}")
    
    # 4. Use the conversation history and user preferences to generate a more contextual response
    print("\n4. Generating contextual response using memory...")
    
    # Pull user preferences from memory to personalize the response
    user_prefs = memory.search("preferences", "user_data")
    
    if user_prefs:
        user_name = user_prefs[0]["metadata"].get("name", "there")
        user_interests = user_prefs[0]["metadata"].get("travel", {}).get("interests", [])
        
        # Generate a personalized response based on memory
        contextualized_response = f"Thanks {user_name}! Based on your interests in {', '.join(user_interests)}, " \
                                 f"I'll create a Tokyo itinerary focusing on cultural sites, food, and shopping."
        
        print(f"\nAgent: {contextualized_response}")
        
        # Store this response too
        memory.store(
            content=contextualized_response,
            metadata={"type": "agent_message", "timestamp": datetime.now().isoformat()},
            namespace=namespace
        )
    
    # 5. Demonstrate using memory for task persistence
    print("\n5. Demonstrating task persistence with memory...")
    
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
    
    print("Task progress stored in memory.")
    
    # Simulate some work being done
    print("\nWorking on the task...")
    time.sleep(1)  # Simulate task processing
    
    # Update the task progress
    task = memory.get("tokyo_trip_plan", "tasks")
    if task:
        updated_metadata = task["metadata"]
        updated_metadata["progress"] = 0.6
        updated_metadata["completed_steps"].append("create daily itinerary")
        updated_metadata["pending_steps"].remove("create daily itinerary")
        
        memory.update(
            memory_id="tokyo_trip_plan",
            metadata=updated_metadata,
            namespace="tasks"
        )
        
        print("Task progress updated in memory.")
    
    # 6. Search for memories
    print("\n6. Searching memories for 'Tokyo'...")
    tokyo_memories = memory.search("Tokyo", namespace)
    print(f"Found {len(tokyo_memories)} memories related to Tokyo.")
    
    # Display a sample of the retrieved memories
    if tokyo_memories:
        print("\nSample memory content:")
        print(tokyo_memories[0]["content"])
    
    print("\nMemory demo complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()