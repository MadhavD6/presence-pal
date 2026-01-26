from backend.services.vector import vector_service

print("--- Testing Dynamic Engine Selection (Small Tenant) ---")
vector_service.load_index()
print(f"Selected Engine Type: {type(vector_service.engine).__name__}")

print("\n--- Testing Dynamic Engine Selection (Medium Tenant / Force FAISS) ---")
vector_service.SMALL_TENANT_LIMIT = 0 # Force FAISS
vector_service.load_index()
print(f"Selected Engine Type: {type(vector_service.engine).__name__}")
