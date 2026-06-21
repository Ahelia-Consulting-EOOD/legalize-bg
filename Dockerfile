# legalize-bg MCP server image (2.x-c packaging).
#
# The image carries ONLY the application. The corpus (Markdown + .git) and
# the derived `catalog.db` (~1 GB, git-derived, gitignored) are mounted at
# runtime rather than baked in.
#
# Build:
#   docker build -t legalize-bg-mcp .
#
# Build the index once (host or a one-off container):
#   docker run --rm -v "$PWD:/corpus" --entrypoint python legalize-bg-mcp \
#       -m index.build --corpus /corpus --db /corpus/catalog.db
#
# Run the stdio MCP server (the MCP host attaches over stdin/stdout; -i):
#   docker run --rm -i -v "$PWD:/corpus" legalize-bg-mcp \
#       --db /corpus/catalog.db --corpus /corpus
FROM python:3.12-slim

WORKDIR /app

# git is needed at runtime — historical get_law/diff shell out to `git`,
# and index.build reads git HEAD. (lxml/pyyaml/fastmcp install from wheels,
# so no C build toolchain is required.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Install the package (deps + the `legalize-bg-mcp` console entry point).
# Only the Python packages are copied; the corpus is mounted at runtime.
COPY pyproject.toml ./
COPY mcp_server/ ./mcp_server/
COPY index/ ./index/
COPY fetcher/ ./fetcher/
RUN pip install --no-cache-dir .

# stdio transport (FastMCP default). Default CMD assumes the repo is mounted
# at /corpus; override --db/--corpus as needed.
ENTRYPOINT ["legalize-bg-mcp"]
CMD ["--db", "/corpus/catalog.db", "--corpus", "/corpus"]
