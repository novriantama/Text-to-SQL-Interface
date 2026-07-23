"""Streamlit User Interface Dashboard for Text-to-SQL Interface with Multi-Signal Confidence Scoring."""

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
    "Translate plain English questions into safe, executable SQL queries with automated guardrails & multi-signal confidence scoring."
)

question_input = st.text_input(
    "Ask a database question:",
    placeholder="e.g. Show top 5 orders by revenue for the current month"
)

if st.button("Generate & Execute Query", type="primary"):
    if not question_input.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Analyzing schema, evaluating guardrails, and executing query..."):
            try:
                pipeline = get_pipeline_use_case()
                response = pipeline.execute(QueryRequest(question=question_input))

                # Check if question is ambiguous and needs clarification
                if response.clarification_needed and response.clarification_options:
                    st.info("🤔 **Ambiguous Question Detected!** Please select one of the following business interpretations:")
                    for idx, option in enumerate(response.clarification_options, 1):
                        with st.expander(f"Option {idx}: {option.label}", expanded=True):
                            st.write(f"**Meaning:** {option.description}")
                            st.code(option.example_sql, language="sql")
                else:
                    # Prominent Confidence Score Display
                    overall_pct = round(response.confidence.overall_score * 100, 1)
                    badge_color = "🟢" if response.confidence.is_high_confidence() else ("🟡" if overall_pct >= 60.0 else "🔴")

                    st.markdown(f"### {badge_color} Confidence Score: **{overall_pct}%**")

                    with st.expander("📊 Detailed Confidence Score Breakdown", expanded=True):
                        m1, m2, m3, m4, m5 = st.columns(5)
                        m1.metric("Syntax Validity", f"{round(response.confidence.syntax_validity * 100)}%")
                        m2.metric("Back-Translation", f"{round(response.confidence.back_translation_match * 100)}%")
                        m3.metric("Result Sanity", f"{round(response.confidence.result_sanity_score * 100)}%")
                        m4.metric("Multi-Query Agreement", f"{round(response.confidence.multi_query_consensus * 100)}%")
                        m5.metric("Schema Coverage", f"{round(response.confidence.schema_coverage * 100)}%")

                    # Anomaly Warnings (if any)
                    if response.warnings:
                        for warn in response.warnings:
                            st.warning(f"⚠️ {warn}")

                    st.subheader("Generated SQL Query")
                    st.code(response.generated_sql, language="sql")

                    st.subheader("Explanation")
                    st.write(response.explanation)

                    # Multi-Query Alternative Approach (if available)
                    if response.alternative_sql and response.alternative_sql != response.generated_sql:
                        with st.expander("🔀 Multi-Query Independent Alternative Approach", expanded=False):
                            st.code(response.alternative_sql, language="sql")
                            if response.alternative_explanation:
                                st.caption(response.alternative_explanation)

                    if response.results and response.results.data:
                        st.subheader(f"Query Results ({response.results.rows_returned} rows returned in {response.results.execution_time_ms}ms)")
                        st.dataframe(response.results.data)
                    else:
                        st.info("No data returned or query executed without output.")

            except Exception as err:
                st.error(f"Error executing query: {err}")
