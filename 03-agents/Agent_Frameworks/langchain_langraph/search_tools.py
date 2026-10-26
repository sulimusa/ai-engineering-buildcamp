from typing import List

from gitsource import GithubRepositoryDataReader, chunk_documents
from minsearch import AppendableIndex


class SearchTools:
    """Documentation search tools backed by a MinSearch index.

    This recreates the knowledge base used in the earlier agentic search
    lessons: it reads the Evidently docs repository, chunks the documents,
    and indexes them for keyword search.
    """

    def __init__(
        self,
        repo_owner: str = "evidentlyai",
        repo_name: str = "docs",
        chunk_size: int = 3000,
        chunk_step: int = 1500,
    ):
        reader = GithubRepositoryDataReader(
            repo_owner,
            repo_name,
            allowed_extensions={"md", "mdx"},
        )

        parsed_docs = reader.read()

        self.files = list(parsed_docs)
        self.chunked_docs = chunk_documents(
            self.files,
            size=chunk_size,
            step=chunk_step,
)

        self.index = AppendableIndex(
            text_fields=["title", "description", "content"],
            keyword_fields=["filename"],
        )
        self.index.fit(self.chunked_docs)

    def search(self, query: str, num_results: int = 5) -> List[dict]:
        """Search the documentation index for relevant chunks."""
        return self.index.search(
            query,
            num_results=num_results,
        )

    def get_file(self, filename: str) -> str:
        """Return the full text of a documentation file by filename."""
        matching_chunks = [
            chunk
            for chunk in self.chunked_docs
            if chunk.get("filename") == filename
        ]

        if not matching_chunks:
            raise FileNotFoundError(
                f"Documentation file not found in index: {filename}"
            )

        # Chunks may overlap, so return them in document order.
        ordered = sorted(
            matching_chunks,
            key=lambda chunk: chunk.get("start", 0),
        )

        return "\n\n".join(chunk["content"] for chunk in ordered)


def create_search_tools() -> SearchTools:
    """Create the shared Evidently documentation search tools."""
    return SearchTools()
