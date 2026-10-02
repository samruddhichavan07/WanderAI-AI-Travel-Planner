from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma

# ---- Load the vector store (RAG retriever) ----
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 8})  # top 8 relevant places

# ---- Load the LLM ----
llm = ChatOllama(model="llama3.2:1b")


def generate_itinerary(destination, days, budget, interests):
    # Step 1: Retrieve relevant places using RAG
    query = f"{destination} {interests} tourist attractions"
    retrieved_docs = retriever.invoke(query)

    # Step 2: Keep only docs that actually mention the destination
    relevant_docs = [d for d in retrieved_docs if destination.lower() in d.page_content.lower()]
    docs_to_use = relevant_docs if relevant_docs else retrieved_docs
    context = "\n".join([doc.page_content for doc in docs_to_use])

    # Step 3: Build the prompt for the LLM
    prompt = f"""You are a helpful AI travel planner.

Here are real places from a database, relevant to {destination}:
{context}

User request:
- Destination: {destination}
- Number of days: {days}
- Budget: {budget}
- Interests: {interests}

IMPORTANT RULES:
- Only use place names that appear in the list above. Do not invent, assume, or add places not listed.
- If there are fewer places than days, reuse them sensibly across days rather than making up new ones.
- Do NOT suggest unrelated cities, routes, or transport between cities not mentioned above.
- Keep the entire plan focused only on {destination} itself.

Create a day-wise itinerary. For each day, suggest 2-3 places, roughly estimate
costs, and keep it realistic for the given budget. Format clearly with "Day 1:",
"Day 2:", etc. Keep the tone concise and practical.
"""

    # Step 4: Get the LLM's response
    response = llm.invoke(prompt)
    return response.content


# ---- Test it directly ----
if __name__ == "__main__":
    result = generate_itinerary(
        destination="Delhi",
        days=3,
        budget="₹10000",
        interests="historical monuments"
    )
    print(result)