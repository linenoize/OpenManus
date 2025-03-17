# OpenManus TODO List

This file tracks planned improvements and unfinished features in the OpenManus project.

## File Management System

- [x] Implement local storage backend
- [x] Implement Git storage backend
- [x] Implement Google Drive storage backend
- [ ] Implement OneDrive storage backend
  - Current implementation is a placeholder
  - Need to add Microsoft Graph API integration
  - Implement authentication flow (similar to Google Drive)
  - Create proper error handling and path management

## Memory System

- [x] Implement basic memory storage and retrieval
- [x] Enhance memory search with vector embeddings
  - [x] Replace simple text matching with semantic search
  - [x] Integrate with vector database for efficient similarity search
  - [x] Add memory relevance scoring system
  - [x] Implement memory chunking for long texts

## Vector Database

- [x] Create dedicated vector database tool
  - [x] Implement embedding generation (using sentence-transformers)
  - [x] Create vector storage and retrieval mechanism
  - [x] Add similarity search functionality
  - [x] Integrate with memory system for enhanced recall
  - [ ] Support multiple vector database backends beyond FAISS

## Integration and Testing

- [ ] Create comprehensive test suite for all tools
- [ ] Add examples for each major component
- [ ] Improve error handling and graceful fallbacks
- [ ] Create monitoring system for tool usage and performance

## Documentation

- [ ] Document all APIs with consistent format
- [ ] Create architecture diagrams
- [ ] Add developer getting started guide
- [ ] Document configuration options for all tools