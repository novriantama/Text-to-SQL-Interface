"""Streamlit User Interface Dashboard for Text-to-SQL Interface."""

import streamlit as st
from src.domain.entities.query import QueryRequest
from src.presentation.api.dependencies import get_pipeline_use_case

st.set_page_config(
    page_title="Text-to-SQL Interface with Guardrails",
    page_icon="🔍",
    layout="wide"
)

st.title("🛡️ Enterprise Text-to-SQL Interface")
st.markdown(
    "Translate plain English questions into safe, executable SQL queries with automated guardrails & hallucination scoring."
)

question_input = st.text_input(
    "Ask a database question:",
    placeholder="e.g. Show top 5 orders by revenue for the current month"
)

if st.button("Generate & Execute Query", type="primary"):
    if not question_input.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Analyzing schema, checking guardrails, and executing query..."):
            try:
                pipeline = get_pipeline_use_case()
                response = pipeline.execute(QueryRequest(question=question_input))

                st.subheader("Generated SQL Query")
                st.code(response.generated_sql, language="sql")

                st.subheader("Explanation")
                st.write(response.explanation)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Overall Confidence", f"{round(response.confidence.overall_score * 100, 1)}%")
                with col2:
                    st.metric("Guardrails Passed", "YES" if response.guardrails_passed else "NO")

                if response.results and response.results.data:
                    st.subheader(f"Query Results ({response.results.rows_returned} rows returned)")
                    st.dataframe(response.results.data)
                else:
                    st.info("No data returned or query executed without output.")

            except Exception as err:
                st.error(f"Error executing query: {err}")
