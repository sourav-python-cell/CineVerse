import streamlit as st
import pandas as pd
import numpy as np
import os
import pymongo
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# MongoDB connection for search history tracking
_client = pymongo.MongoClient(st.secrets["MONGO_URI"])
_db = _client['demoDb']
search_history_col = _db['search_history']

def log_search(username: str, movie_title: str):
    """Log a user's movie search query with a timestamp to MongoDB."""
    search_history_col.insert_one({
        'username': username,
        'searched_movie': movie_title,
        'timestamp': datetime.now()
    })

def get_recent_searches(username: str, limit: int = 5):
    """Retrieve the most recent searches for a given user."""
    results = search_history_col.find(
        {'username': username},
        {'_id': 0, 'searched_movie': 1, 'timestamp': 1}
    ).sort('timestamp', pymongo.DESCENDING).limit(limit)
    return list(results)

# Auth Guard
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("Login first")
    if st.button("Go to Login Page", type="tertiary", width="stretch"):
        st.switch_page("pages/home.py")
    st.stop()

# --- Sidebar: Recent Search History ---
with st.sidebar:
    st.markdown("### 🕐 Your Recent Searches")
    recent = get_recent_searches(st.session_state.logged_in_user['user_name'])
    if recent:
        for entry in recent:
            ts = entry['timestamp'].strftime("%d %b, %H:%M")
            st.markdown(f"🎬 **{entry['searched_movie']}** `{ts}`")
    else:
        st.caption("No search history yet. Try the AI Matchmaker!")
    st.write("---")

st.header("Your AI Entertainment Universe")
st.markdown(f"Welcome back, {st.session_state.logged_in_user['user_name']}! Discover movies, anime, series, documentaries and more - curate by AI just for you.")

st.title("AI Movie Recommendations")
st.write("Use our AI model to find movies similar to ones you love, or manually filter to find your perfect match.")

@st.cache_data
def load_combined_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    movies_path = os.path.join(base_dir, "data", "movies.csv")
    indian_movies_path = os.path.join(base_dir, "data", "indian movies.csv")
    
    df1, df2 = pd.DataFrame(), pd.DataFrame()
    
    # Load Hollywood/Global Movies
    if os.path.exists(movies_path):
        # use on_bad_lines instead of error_bad_lines for newer pandas
        try:
            df1 = pd.read_csv(movies_path, on_bad_lines='skip')
        except:
            df1 = pd.read_csv(movies_path, error_bad_lines=False)
        df1.rename(columns={'movie': 'title', 'runtime': 'runtime'}, inplace=True)
        df1['industry'] = 'Hollywood / Global'
        
    # Load Indian/Bollywood Movies
    if os.path.exists(indian_movies_path):
        try:
            df2 = pd.read_csv(indian_movies_path, on_bad_lines='skip')
        except:
            df2 = pd.read_csv(indian_movies_path, error_bad_lines=False)
        df2.rename(columns={
            'Movie Name': 'title', 
            'Timing(min)': 'runtime', 
            'Rating(10)': 'rating', 
            'Genre': 'genre', 
            'Language': 'language', 
            'Votes': 'votes'
        }, inplace=True)
        df2['industry'] = 'Bollywood / Indian'
        
    if df1.empty and df2.empty:
        return pd.DataFrame()
        
    # Combine both datasets
    df = pd.concat([df1, df2], ignore_index=True)
    
    # Standardize missing values
    for col in ['title', 'genre', 'description', 'stars', 'director', 'certificate', 'language']:
        if col in df.columns:
            df[col] = df[col].fillna('')
            
    # Clean up ratings
    if 'rating' in df.columns:
        df['rating'] = pd.to_numeric(df['rating'].replace('-', 0), errors='coerce').fillna(0)
        
    # AI Feature Engineering: Create a unified content string for the AI model to learn from
    df['combined_features'] = df['genre'] + ' ' + df.get('description', '') + ' ' + df.get('language', '') + ' ' + df.get('director', '') + ' ' + df['industry']
    
    return df

@st.cache_resource
def train_ai_model(df):
    # Train the AI model using TF-IDF Vectorization on the combined content features
    vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
    tfidf_matrix = vectorizer.fit_transform(df['combined_features'])
    return vectorizer, tfidf_matrix

def get_recommendations(title, df, tfidf_matrix, top_n=10):
    # Find the index of the movie the user selected
    idx_list = df[df['title'].str.lower() == title.lower()].index.tolist()
    if not idx_list:
        return pd.DataFrame()
    idx = idx_list[0]
    
    # Calculate cosine similarity scores
    sim_scores = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()
    
    # Get top_n most similar movies (excluding itself)
    top_indices = np.argsort(sim_scores)[-(top_n+1):-1][::-1]
    
    # Return the recommended movies
    return df.iloc[top_indices]


df = load_combined_data()

if df.empty:
    st.error("Dataset not found. Please ensure both 'movies.csv' and 'indian movies.csv' exist in the data folder.")
    st.stop()

# Train AI Model
with st.spinner("Training AI Model on combined datasets..."):
    vectorizer, tfidf_matrix = train_ai_model(df)


# UI Layout - 2 Tabs to keep it simple but powerful
tab1, tab2 = st.tabs(["🤖 AI Matchmaker", "🎛️ Manual Filters"])

# Tab 1: AI Matchmaker
with tab1:
    st.subheader("Find Similar Content")
    st.write("Select a movie you liked, and our AI model will recommend similar movies based on content, genre, and description.")
    
    movie_list = df['title'].dropna().unique()
    selected_movie = st.selectbox("Search for a movie:", options=[""] + sorted(list(movie_list)))
    
    if st.button("Find Similar Matches", type="primary", width="stretch") and selected_movie:
        log_search(st.session_state.logged_in_user['user_name'], selected_movie)
        with st.spinner("AI is analyzing movies..."):
            recs = get_recommendations(selected_movie, df, tfidf_matrix)
            
            if recs.empty:
                st.warning("Could not find recommendations.")
            else:
                st.success("Here are your AI-curated recommendations:")
                for i, row in recs.iterrows():
                    with st.container(border=True):
                        st.subheader(row.get('title', 'Unknown Title'))
                        genre = row.get('genre', 'N/A').strip()
                        rating = row.get('rating', 0)
                        industry = row.get('industry', 'N/A')
                        desc = row.get('description', '')
                        
                        st.caption(f"**Genre:** {genre} | **Rating:** {rating} ⭐ | **Industry:** {industry}")
                        if desc:
                            st.write(desc)

# Tab 2: Manual Filters
with tab2:
    st.subheader("Filter Content manually")
    
    # Extract unique genres
    genres = set()
    for g_list in df['genre'].dropna():
        for g in str(g_list).split(','):
            g_clean = g.strip()
            if g_clean:
                genres.add(g_clean)
    genres_list = sorted(list(genres))
    
    col1, col2 = st.columns(2)
    with col1:
        selected_genre = st.selectbox("Genre", options=["Any"] + genres_list)
        selected_industry = st.selectbox("Movie Industry", options=["Any", "Hollywood / Global", "Bollywood / Indian"])
        
    with col2:
        min_rating = st.slider("Minimum Rating (IMDb)", min_value=0.0, max_value=10.0, value=6.0, step=0.5)
    
    if st.button("Apply Filters", width="stretch", type="primary"):
        with st.spinner("Filtering datasets..."):
            filtered_df = df.copy()
            
            if selected_genre != "Any":
                filtered_df = filtered_df[filtered_df['genre'].str.contains(selected_genre, case=False, na=False)]
                
            if selected_industry != "Any":
                filtered_df = filtered_df[filtered_df['industry'] == selected_industry]
                
            filtered_df = filtered_df[filtered_df['rating'] >= min_rating]
            filtered_df = filtered_df.sort_values(by='rating', ascending=False)
            
            st.write("---")
            if filtered_df.empty:
                st.warning("No matches found. Try adjusting your filters.")
            else:
                st.success(f"Found {len(filtered_df)} matches!")
                for i, row in filtered_df.head(10).iterrows():
                    with st.container(border=True):
                        st.subheader(row.get('title', 'Unknown Title'))
                        genre = row.get('genre', 'N/A').strip()
                        rating = row.get('rating', 0)
                        industry = row.get('industry', 'N/A')
                        desc = row.get('description', '')
                        
                        st.caption(f"**Genre:** {genre} | **Rating:** {rating} ⭐ | **Industry:** {industry}")
                        if desc:
                            st.write(desc)

if st.button("Logout",type="secondary",width="stretch"):
    st.session_state['logged_in'] = False
    st.rerun()