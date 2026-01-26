#!/bin/bash

echo "Starting Cloudflare Tunnel for localhost:8080..."
cloudflared tunnel --url http://localhost:8080
