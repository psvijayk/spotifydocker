import os
import requests
import streamlit as st

st.set_page_config(
    page_title="Hybrid RAG Assistant",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Hybrid RAG + Knowledge Graph")
st.caption("FAISS + Neo4j + FastAPI + Guardrails")

api_url = st.sidebar.text_input("Backend URL", os.getenv("API_URL", "http://localhost:8000"))

st.sidebar.markdown("### 1. Ingest")
uploaded = st.sidebar.file_uploader("Upload PDF", type=["pdf"])

if uploaded and st.sidebar.button("Ingest PDF"):
    try:
        response = requests.post(
            f"{api_url}/ingest",
            files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
            timeout=300,
        )
        if response.ok:
            st.sidebar.success(response.json())
        else:
            st.sidebar.error(response.text)
    except Exception as exc:
        st.sidebar.error(str(exc))

st.markdown("### Ask a question")
question = st.text_area(
    "Question",
    placeholder="Ask something about your indexed documents...",
    height=120,
)

if st.button("Ask", type="primary") and question.strip():
    with st.spinner("Searching vector database and knowledge graph..."):
        try:
            response = requests.post(
                f"{api_url}/ask",
                json={"question": question},
                timeout=180,
            )

            if not response.ok:
                st.error(response.text)
            else:
                data = response.json()

                st.markdown("## Answer")
                st.write(data["answer"])

                if data.get("guardrail_flags"):
                    st.warning("Guardrail flags: " + ", ".join(data["guardrail_flags"]))

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Vector sources")
                    for source in data.get("sources", []):
                        if source["type"] == "vector":
                            st.write(
                                f"- {source['source']} / {source['chunk_id']} "
                                f"(score={source['score']})"
                            )

                with col2:
                    st.markdown("### Knowledge Graph")
                    for item in data.get("graph_context", []):
                        st.json(item)

        except Exception as exc:
            st.error(str(exc))
