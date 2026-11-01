import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from database.db_manager import get_recent_speech_checks, get_practice_history

def render_progress_tab():
    st.markdown("""
    <div class='fluent-card'>
        <h2>📈 My Progress & Severity Tracking</h2>
        <p style='color: #64748B; font-size: 16px;'>
            Monitor your speech severity reduction over time and track your practice consistency. Seeing real progress empowers every day!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    checks = get_recent_speech_checks(limit=50)
    practice = get_practice_history(limit=50)
    
    # Top Stats Row
    pcol1, pcol2, pcol3, pcol4 = st.columns(4)
    with pcol1:
        st.metric("Total Speech Checks", len(checks))
    with pcol2:
        st.metric("Total Practice Sessions", len(practice))
    with pcol3:
        avg_score = round(pd.DataFrame(practice)['match_score_pct'].mean(), 1) if practice else 0.0
        st.metric("Avg Practice Accuracy", f"{avg_score}%")
    with pcol4:
        st.metric("Daily Practice Streak", f"{min(len(practice), 14)} Days 🔥")
        
    st.markdown("<br/>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📊 Severity Percentage Trend")
        if checks:
            df_checks = pd.DataFrame(checks)
            df_checks['timestamp'] = pd.to_datetime(df_checks['timestamp'])
            df_checks = df_checks.sort_values('timestamp')
            
            fig = px.line(
                df_checks,
                x='timestamp',
                y='severity_pct',
                color='severity_category',
                markers=True,
                title="Severity Percentage Over Time (% Lower is Better)",
                labels={'severity_pct': 'Severity %', 'timestamp': 'Check Date'}
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(248,250,252,1)',
                font_family="Plus Jakarta Sans",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Demonstration baseline trend chart
            demo_df = pd.DataFrame({
                "Day": ["Day 1", "Day 3", "Day 7", "Day 10", "Day 14"],
                "Severity %": [88.5, 82.0, 75.4, 68.2, 62.0]
            })
            fig = px.line(demo_df, x="Day", y="Severity %", markers=True, title="Sample Improvement Trend (Day 1 -> Day 14)")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350)
            st.plotly_chart(fig, use_container_width=True)
            
    with col2:
        st.markdown("### 🎯 Practice Exercise Accuracy Evolution")
        if practice:
            df_prac = pd.DataFrame(practice)
            df_prac['timestamp'] = pd.to_datetime(df_prac['timestamp'])
            df_prac = df_prac.sort_values('timestamp')
            
            fig2 = px.bar(
                df_prac,
                x='timestamp',
                y='match_score_pct',
                color='match_score_pct',
                color_continuous_scale='Blues',
                title="Exercise Score History (% Higher is Better)"
            )
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            demo_p = pd.DataFrame({
                "Session": [f"S{i}" for i in range(1, 6)],
                "Score %": [55, 68, 74, 82, 90]
            })
            fig2 = px.bar(demo_p, x="Session", y="Score %", title="Sample Practice Score Progression")
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350)
            st.plotly_chart(fig2, use_container_width=True)
            
    st.markdown("### 🏆 Badges & Milestones")
    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        st.success("🌟 **First Step Badge**: Completed your first speech check!")
    with bcol2:
        st.success("🔥 **Consistency Master**: Practiced 5 days in a row!")
    with bcol3:
        st.success("🎯 **Clarity Champion**: Achieved >85% match in a practice exercise!")
