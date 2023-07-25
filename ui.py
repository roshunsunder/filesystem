import streamlit as st
from indexer import Indexer
from query import QueryDriver

q = QueryDriver()
q.load_from_disk("faiss_index")

def search(string):
    global q
    res = q.query(string)
    for f in res:
        st.markdown(f"[{f}]({f})", unsafe_allow_html=True)

def main():
    st.title("Talk to your File System")
    # Create a search box
    search_query = st.text_input("Enter a search query:")
    st.button(label="Go!", on_click=search(search_query))


if __name__ == "__main__":
    main()