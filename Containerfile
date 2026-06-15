FROM quay.io/hummingbird/python:latest-fips-builder AS builder
USER 0
RUN dnf install -y --setopt=install_weak_deps=False systemd && dnf clean all
WORKDIR /app
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .
RUN mkdir -p /staging/usr/bin /staging/usr/lib64 /staging/usr/lib64/systemd && \
    cp /usr/bin/systemctl /staging/usr/bin/ && \
    cp /usr/bin/journalctl /staging/usr/bin/ && \
    cp /usr/lib64/systemd/libsystemd-shared-*.so /staging/usr/lib64/systemd/ && \
    ldd /usr/bin/systemctl /usr/bin/journalctl | \
    grep "=> /" | awk '{print $3}' | sort -u | \
    xargs -I{} cp -L {} /staging/usr/lib64/ 2>/dev/null || true

FROM quay.io/hummingbird/python:latest-fips

LABEL name="mcp-podman-crunchtools" \
      version="0.2.1" \
      summary="MCP server for Podman container management via the Podman REST API" \
      maintainer="crunchtools.com" \
      org.opencontainers.image.source="https://github.com/crunchtools/mcp-podman" \
      org.opencontainers.image.description="MCP server for Podman container management" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"

COPY --from=builder /app/venv /app/venv
COPY --from=builder /staging/usr/bin/ /usr/bin/
COPY --from=builder /staging/usr/lib64/ /usr/lib64/
COPY --from=builder /staging/usr/lib64/systemd/ /usr/lib64/systemd/
ENV PATH="/app/venv/bin:$PATH"

EXPOSE 8023
ENTRYPOINT ["python", "-m", "mcp_podman_crunchtools"]
