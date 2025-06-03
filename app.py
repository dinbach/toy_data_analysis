import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Διαδραστικός Εξερευνητής Δεδομένων", layout="wide")

st.title("Διαδραστικός Εξερευνητής Δεδομένων")

# Καταχώρηση αρχείου
uploaded_file = st.file_uploader("Ανεβάστε το αρχείο Excel σας", type=["xls", "xlsx"])

if uploaded_file:
    # Ανάγνωση του Excel αρχείου σε DataFrame
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Σφάλμα κατά την ανάγνωση του αρχείου Excel: {e}")
        st.stop()

    # Έλεγχος ύπαρξης στήλης 'Channel'
    if "Channel" not in df.columns:
        st.error("Δεν βρέθηκε η στήλη 'Channel' στα δεδομένα.")
        st.stop()
    channel_column = "Channel"

    # Διαιρούμε τις στήλες _pt, _E, Zll_mass, MET με 1000 για μετατροπή σε GeV
    cols_to_divide = [
        col for col in df.columns
        if col.endswith("_pt") or col.endswith("_E") or col in ["Zll_mass", "MET"]
    ]
    for col in cols_to_divide:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col] / 1000

    st.sidebar.header("Ρυθμίσεις Ιστογράμματος")
    all_columns = df.columns.tolist()

    # Επιλογή στήλης για ιστόγραμμα (μόνο αριθμητικές)
    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
    if not numeric_columns:
        st.error("Δεν βρέθηκαν αριθμητικές στήλες για το ιστόγραμμα.")
        st.stop()
    hist_column = st.sidebar.selectbox("Επιλέξτε στήλη για ιστόγραμμα", options=numeric_columns)

    # Δυνατότητα εισαγωγής αριθμού διαστημάτων (bins)
    default_bins = 10 if 10 <= len(df) else max(1, len(df) // 10)
    bins = st.sidebar.number_input(
        "Εισάγετε αριθμό διαστημάτων (bins)",
        min_value=1,
        max_value=100,
        value=default_bins,
        step=1
    )

    # Ρυθμίσεις φιλτραρίσματος
    st.sidebar.header("Φιλτράρισμα Δεδομένων")
    filter_columns = st.sidebar.multiselect(
        "Επιλέξτε στήλες για φίλτρο εύρους ή τιμών", options=all_columns, default=[]
    )

    filtered_df = df.copy()

    # Εφαρμογή φίλτρων
    for col in filter_columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            min_val = float(df[col].min())
            max_val = float(df[col].max())
            # Ρυθμίζουμε τα βήματα ανάλογα με το όνομα της στήλης
            if col.endswith("_pt") or col.endswith("_E") or col in ["Zll_mass", "MET"]:
                step = 1.0
            elif col.endswith("_eta") or col.endswith("_phi"):
                step = 0.1
            else:
                step = (max_val - min_val) / 100 if max_val != min_val else 1.0
            user_min = st.sidebar.number_input(
                f"Ελάχιστη τιμή για {col}",
                min_value=min_val,
                max_value=max_val,
                value=min_val,
                step=step
            )
            user_max = st.sidebar.number_input(
                f"Μέγιστη τιμή για {col}",
                min_value=min_val,
                max_value=max_val,
                value=max_val,
                step=step
            )
            filtered_df = filtered_df[(filtered_df[col] >= user_min) & (filtered_df[col] <= user_max)]
        else:
            unique_vals = df[col].dropna().unique().tolist()
            selected_vals = st.sidebar.multiselect(f"Φιλτράρισμα τιμών για {col}", options=unique_vals, default=unique_vals)
            filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]

    # Δημιουργία πίνακα πλήθους ανά κανάλι και συνολικού
    total_count = filtered_df.shape[0]
    counts = filtered_df[channel_column].value_counts()
    counts_df = counts.reset_index()
    counts_df.columns = [channel_column, "Πλήθος"]
    total_row = pd.DataFrame({channel_column: ["Σύνολο"], "Πλήθος": [counts_df["Πλήθος"].sum()]})
    counts_df = pd.concat([counts_df, total_row], ignore_index=True)

    st.subheader("Πλήθη Καναλιών μετά το Φιλτράρισμα")
    st.table(counts_df)

    # Έλεγχος εάν η στήλη για ιστόγραμμα υπάρχει μετά το φιλτράρισμα
    if hist_column not in filtered_df.columns:
        st.error("Η επιλεγμένη στήλη για ιστόγραμμα δεν βρέθηκε μετά το φιλτράρισμα.")
        st.stop()

    # Δημιουργία διαδραστικού ιστογράμματος Plotly με overlay
    fig = px.histogram(
        filtered_df,
        x=hist_column,
        color=channel_column,
        nbins=bins,
        labels={hist_column: hist_column, "count": "Αριθμός Εγγραφών"},
        title=f"Ιστόγραμμα της στήλης {hist_column} διαφοροποιημένο ανά {channel_column}"
    )
    fig.update_layout(barmode='overlay', legend_title=channel_column)
    fig.update_traces(opacity=0.7)

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Παρακαλώ ανεβάστε ένα αρχείο Excel για να ξεκινήσετε.")
