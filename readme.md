## PaliAPI

An end to end RAG web applcation for Colipali-based RAG system.

Components:

1. Embeddings Service

2. Postgres DB with pgvector extension

3. Create Collection, Upsert, Delete, Search, Update, Delete Collection

### Models:

- **User**: Represents an individual user.
- **Collection**: Represents a collection of documents, owned by a user.
- **Document**: Each document belongs to a specific collection.
- **Page**: Each page belongs to a specific document and contains the embeddings.

### Endpoints:

1. **Health Check**  
   **Method**: `GET /health`  
   **Purpose**: Check if the API is running properly.  
   **Response**: `{ "status": "ok" }`


# create index (collection, documents, pages with embeddings all in one go)
# search index (search for pages with embeddings similar to a given query)
# delete index (delete a collection and all its documents and pages)
# Emeddings - send a document or a query, get embeddings back


2. **Create Collection**  
   **Method**: `POST /collections`  
   **Request Body**: `{ "name": "Research Papers" }`  
   **Purpose**: Create a new collection for a specific user.  
   **Response**: `{ "id": 1, "message": "Collection created successfully" }`

3. **List User's Collections**  
   **Method**: `GET /collections`  
   **Purpose**: Retrieve all collections for a specific user.  
   **Response**:

   ```json
   {
     "collections": [
       { "id": 1, "name": "Research Papers", "metadata": { "key": "value" } },
       { "id": 2, "name": "Book Summaries", "metadata": { "key": "value" } }
     ]
   }
   ```

4. **Get Collection Details**  
   **Method**: `GET /collections/{collection_id}`  
   **Purpose**: Retrieve a collection for a specific user.  
   **Response**:

   ```json
   {
     "id": 1,
     "name": "Research Papers",
     "metadata": { "key": "value" }
   }
   ```

5. **Update Collection**  
   **Method**: `PUT /collections/{collection_id}`  
   **Request Body**: `{ "name": "New Collection Name" }`  
   **Purpose**: Update a collection's name by its `id` for a specific user.  
   **Response**: `{ "message": "Collection updated successfully" }`

6. **Delete Collection**  
   **Method**: `DELETE /collections/{collection_id}`  
   **Purpose**: Delete a collection by its `id` for a specific user.  
   **Response**: `{ "message": "Collection deleted successfully" }`



7. **Get Document by ID in a Collection**  
   **Method**: `GET /collections/{collection_id}/documents/{document_id}`  
   **Purpose**: Retrieve a document from a specific collection by its `id`.  
   **Response**:

   ```json
   {
     "id": 1,
     "content": "The document text",
      "metadata": { "key": "value" }
   }
   ```

8. **List All Documents in a Collection**  
   **Method**: `GET /collections/{collection_id}/documents`  
   **Purpose**: Retrieve a list of all documents in a specific collection.  
   **Response**:

   ```json
   {
     "documents": [
       { "id": 1, "content": "Document 1 text" },
       { "id": 2, "content": "Document 2 text" }
     ]
   }
   ```

# bulk upsert with files (C and U) - we create pages with embeddings here


9. **Upsert Document to Collection**  
   **Method**: `POST collections/{collection_id}/documents`  
   **Request Body**: `{ "content": "The document text" }`  
   **Purpose**: Upserts a new document to a specific collection.  
   **Response**: `{ "id": 1, "message": "Document added successfully" }`

10. **Delete Document from a Collection**  
    **Method**: `DELETE /collections/{collection_id}/documents/{document_id}`  
    **Purpose**: Delete a document by its `id` from a specific collection.  
    **Response**: `{ "message": "Document deleted successfully" }`

11. **Query Documents in a Collection**  
    **Method**: `POST /collections/{collection_id}/query`  
    **Request Body**: `{ "query": "search text", "top_k": 5 }`  
    **Purpose**: Takes a query text, generates embeddings, and retrieves the top `k` documents in a specific collection based on the similarity score.  


11. **Embeddings Service**  
    **Method**: `POST /embeddings`  
    **Request Body**: `{ "texts": ["text1", "text2", ...] }`  
    **Purpose**: Generate embeddings for a list of texts.  
    **Response**:

```json
{
  "embeddings": [
    [...],
    [...],
    ...
  ]
}
```

---
