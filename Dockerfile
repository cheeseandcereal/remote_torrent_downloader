FROM linuxserver/unrar:latest AS unrar
FROM python:3.12-alpine AS base

WORKDIR /usr/src/app
RUN apk --no-cache upgrade && apk --no-cache add lftp

FROM base AS builder
# Install build dependencies
# RUN apk --no-cache add make
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

FROM base AS release
# Copy compiled unrar
COPY --from=unrar /usr/bin/unrar-alpine /usr/bin/unrar
# Copy the installed python dependencies from the builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
# Copy the app
COPY --chown=1000:1000 . .

USER 1000:1000
CMD [ "python", "-m", "downloader.main" ]
